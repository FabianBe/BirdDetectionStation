import { config } from "process";

const tf = require('@tensorflow/tfjs-node');
const load = require('audio-loader')
const SampleRate = require('node-libsamplerate');
const fs = require('fs');

const LABELS = require('./labels');

const MODEL_JSON = 'file://model/model.json'

const CONFIG = {
    sampleRate: 48000,
    specLength: 3,
    sigmoid: 1.0,
    minConfidence: 0.5,
    labels: null,
}

let MODEL = null;
var RESULTS = [];
var AUDIO_DATA = [];


/////////////////////////  Build SimpleSpecLayer  /////////////////////////
class SimpleSpecLayer extends tf.layers.Layer {
    constructor(config) {
        super(config);

        // For now, let's work with hard coded values to avoid strange errors when reading the config
        this.spec_shape = [257, 384];
        this.frame_length = 512;
        this.frame_step = 374;
    }

    build(inputShape) {
        this.mag_scale = this.addWeight('magnitude_scaling', [], 'float32', tf.initializers.constant({ value: 1.0 }));
    }

    computeOutputShape(inputShape) { return [inputShape[0], this.spec_shape[0], this.spec_shape[1], 1]; }

    call(input, kwargs) {

        // Perform STFT    
        var spec = tf.signal.stft(input[0].squeeze(),
            this.frame_length,
            this.frame_step)

        // Cast from complex to float
        spec = tf.cast(spec, 'float32');

        // Convert to power spectrogram
        spec = tf.pow(spec, 2.0);

        // Convert magnitudes using nonlinearity
        spec = tf.pow(spec, tf.div(1.0, tf.add(1.0, tf.exp(this.mag_scale.read()))));

        // Normalize values between 0 and 1
        spec = tf.div(tf.sub(spec, tf.min(spec)), tf.max(spec));

        // Swap axes to fit output shape
        spec = tf.transpose(spec);

        // Add channel axis        
        spec = tf.expandDims(spec, -1);

        // Add batch axis        
        spec = tf.expandDims(spec, 0);

        return spec;

    }

    static get className() { return 'SimpleSpecLayer'; }
}

tf.serialization.registerClass(SimpleSpecLayer);

/////////////////////////  Build GlobalExpPool2D Layer  /////////////////////////
function logmeanexp(x, axis, keepdims, sharpness) {
    let xmax = tf.max(x, axis, true);
    let xmax2 = tf.max(x, axis, keepdims);
    x = tf.mul(sharpness, tf.sub(x, xmax));
    let y = tf.log(tf.mean(tf.exp(x), axis, keepdims));
    y = tf.add(tf.div(y, sharpness), xmax2);
    return y
}

class GlobalLogExpPooling2D extends tf.layers.Layer {
    constructor(config) {
        super(config);
    }

    build(inputShape) {
        this.sharpness = this.addWeight('sharpness', [1], 'float32', tf.initializers.constant({ value: 2.0 }));
    }

    computeOutputShape(inputShape) { return [inputShape[0], inputShape[3]]; }

    call(input, kwargs) {

        return logmeanexp(input[0], [1, 2], false, this.sharpness.read());//.read().dataSync()[0]); 

    }

    static get className() { return 'GlobalLogExpPooling2D'; }
}

tf.serialization.registerClass(GlobalLogExpPooling2D);

/////////////////////////  Build Sigmoid Layer  /////////////////////////
class SigmoidLayer extends tf.layers.Layer {
    constructor(config) {
        super(config);
        this.config = config;
    }

    build(inputShape) {
        this.kernel = this.addWeight('scale_factor', [1], 'float32', tf.initializers.constant({ value: 1.0 }));
    }

    computeOutputShape(inputShape) { return inputShape; }

    call(input, kwargs) {

        return tf.sigmoid(tf.mul(input[0], CONFIG.sigmoid))

    }

    static get className() { return 'SigmoidLayer'; }
}

tf.serialization.registerClass(SigmoidLayer);


exports.loadModel = async function loadModel() {

    // Load model
    if (MODEL == null) {
        console.log('Loading model...');
        MODEL = await tf.loadLayersModel(MODEL_JSON);
        //CONFIG.labels = MODEL.getLayer('SIGMOID').config.labels;
        CONFIG.labels = LABELS;
        console.log('...done loading model!');
    }

}

exports.predict = async function predict(audioFile) {

    for (i = 0; i < 3; ++i) {

        await loadAudioFile(audioFile);

        let model = MODEL;
        let audioData = AUDIO_DATA;

        const audioTensor = tf.tensor1d(audioData)
        RESULTS = [];


        // Slice and expand
        var cunkLength = CONFIG.sampleRate * CONFIG.specLength;
        for (var i = 0; i < audioTensor.shape[0] - cunkLength; i += CONFIG.sampleRate) {


            if (i + cunkLength > audioTensor.shape[0]) i = audioTensor.shape[0] - cunkLength;
            const chunkTensor = audioTensor.slice(i, cunkLength).expandDims(0);
            // Make prediction
            const prediction = await model.predict(chunkTensor);

            // Get label
            const index = prediction.argMax(1).dataSync()[0];
            const score = prediction.dataSync()[index];

            console.log(index, CONFIG.labels[index], score);

            if (!isEnvironmentNoise(index)) {
                let birdName = CONFIG.labels[index].split('_')[1];
                RESULTS.push({ 'Common Name': birdName, 'Confidence': score });
            }
        }

    }

    RESULTS.sort((cName1, cName2) => cName2['Confidence'] - cName1['Confidence'])
    let unique_results = [];
    RESULTS.forEach(res => {
        if (!unique_results.some(item => item['Common Name'] === res['Common Name'])) {
            if (typeof res['Common Name'] === 'string' && notInBlacklist(res['Common Name'])) {
                unique_results.push(res);
            }
        }
    })

    return unique_results;

}

function isEnvironmentNoise(index: any) {
    return CONFIG.labels[index] == "Non-Bird_Non-Bird" ||
        CONFIG.labels[index] == "Noise_Noise" ||
        CONFIG.labels[index] == "Non-Bird";
}

function notInBlacklist(birdName: string) {
    birdName = birdName.toLowerCase();
    return birdName != "Rook".toLowerCase() &&
        birdName != "European Pied Flycatcher".toLowerCase() &&
        birdName != "Painted Bunting".toLowerCase() &&
        birdName != "Human".toLowerCase();
}

async function loadAudioFile(filePath) {

    await load(filePath).then((buffer) => {
        console.log(AUDIO_DATA);
        AUDIO_DATA = buffer.getChannelData(0);
    });
}


1