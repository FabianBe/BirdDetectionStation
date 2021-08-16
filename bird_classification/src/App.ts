import * as path from 'path';
import * as express from 'express';
import * as logger from 'morgan';
import * as bodyParser from 'body-parser';
import { Console } from 'console';


const fileUpload = require('express-fileupload');

const birdnet = require('./BirdNET');

// Creates and configures an ExpressJS web server.
class App {

    // ref to Express instance
    public express: express.Application;

    private constructor() {
    }

    public static async CreateAsync() : Promise<App> {
        const app = new App();
        app.express = express();
        app.middleware();
        app.routes();
        await birdnet.loadModel();
        return app;
    }

    // Configure Express middleware.
    private middleware(): void {
        this.express.use(logger('dev'));
        this.express.use(bodyParser.json());
        this.express.use(bodyParser.urlencoded({ extended: false }));
        this.express.use(fileUpload());
    }

    // Configure API endpoints.
    private routes(): void {
        /* This is just to get up and running, and to make sure what we've got is
         * working so far. This function will change when we start to add more
         * API endpoints */
        let router = express.Router();

        router.post('/actions/analyse', async (req, res) => {
            try {
                if (!req.files) {
                    res.send({
                        status: false,
                        message: 'No file uploaded'
                    });
                } else {
                    //Use the name of the input field (i.e. "avatar") to retrieve the uploaded file
                    let file = req.files.wave;
        
                    if (!Array.isArray(file)){

                        //Use the mv() method to place the file in upload directory (i.e. "uploads")
                        file.mv('./uploads/' + file.name);

                       const data = await birdnet.predict('./uploads/' + file.name);

                        console.log(data);

                        //send response
                        res.send({
                            Result: data
                        });
                    }
                }
            } catch (err) {
                res.status(500).send(err);
            }
        });

        // placeholder route handler
        router.get('/', (req, res, next) => {
            res.json({
                message: 'Hello World!'
            });
        });
        this.express.use('/', router);
    }

}

export default App;
