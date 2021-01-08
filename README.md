# GM Maven Gig Dashboard 

### Running the app locally
We suggest you to create a separate virtual environment running Python 3 for this app, and install all of the required dependencies there. Run in Terminal/Command Prompt:

#in new terminal window


```
git clone https://github.com/butlerbt/maven-dash-app
cd maven-dash-app
python3 -m virtualenv venv
```
In UNIX system: 

```
source venv/bin/activate
```

To install all of the required packages to this environment, run:

```
pip install -r requirements.txt
```

and all of the required `pip` packages, will be installed, and the app will be able to run.

To launch the app for development on a VM and then debug on your local machine:
1. Make sure the the app's initializaion statement is as follows:
```
if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port = 3002)
```
2. run the following command on the VM:
```
python app.py
```

3. Now create a tunnel from your local machine to the port its launched on by running the following command in a new terminal window on your local machine:
```
ssh -N -f -L 8884:localhost:3000 bbutler@rmi.org@104.42.97.219 
```
4. Now navigate to local host 8884 from your local machine's browser

### Deploying the app on a heroku server
1. If it is not already installed, install gunicorn
```
pip install gunicorn
```
2. Initialize Heroku, add files to Git, and deploy
```
 heroku create maven-dash # change maven-dash to a unique name
 git add . # add all files to git
 git commit -m 'Initial app boilerplate'
 git push heroku master # deploy code to heroku
 heroku ps:scale web=1  # run the app with a 1 heroku "dyno"
 ```
 ### CI/CD on Heroku

 5. Update the code and redeploy

When you modify app.py with your own code, you will need to add the changes to git and push those changes to heroku.

git status # view the changes
git add .  # add all the changes
git commit -m 'a description of the changes'
git push heroku master

## Data Source for App:

This app requires very specifically formatted data files in order to function. The data files contained in the `/data/` directory were created and formatted using a jupyter notebook in the orginal GM-Maven repo. This notebook and the accompying documentation can be found in notebooks/visualizations/data_prep_for_dash.ipynb within the original GM-Maven repo. 

## Security Credentials:

The current security and login credentials are set up for development purposes only and should be changed before the app is deployed and live on the RMI Report's landing page. The login feature can be edited and removed by editing lines 122-125 and line 148 of app.py. Additional valid login credentials can be added/subtracted by editing `login_credentials.json` in the `/.secret/` directory. This file should follow the format:
```
{
    "ValidUsername1": "ValidPassword1",
    "ValidUsername2": "ValidPassword2",
}
```



