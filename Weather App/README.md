## Weather App
Welcome to the Weather app documentation! 
The Weather app is a command-line application that allows you to easily retrieve weather information for any city around the world. Currently, it lets you check their current temperature, humidity, and wind speed.
You can quickly access these data without the need for complex web searches or navigating through multiple websites.

Key Features:
- Retrieve real-time temperature, wind speed and humidity information for any city.
- Display weather information in a clear and organized tabular format.
- Support for temperature units in Celsius, Fahrenheit, and Kelvin.
- Conversion of wind speed units between meters per second, miles per hour, and kilometers per hour.

Follow this documentation to learn how to install, configure, and effectively use the Weather app to start using it now.

## Table of Contents
1. [Installation](#installation)
2. [Usage](#usage)
3. [Conclusion](#conclusion)
   
## Installation
To use the Weather app, you'll need:
•	Python 3.7 or higher installed on your system.
•	Internet connectivity to make API requests.

### Installation Steps
1.	Python Installation:
-	If you don't have Python installed, visit the official Python website at https://www.python.org to download and install the latest version for your operating system.
-	During the installation process, make sure to check the option to add Python to your system's PATH.

2.	Clone or Download the Weather App:
-	In the repo, click on the "Code" button and select either "Download ZIP" to download the source code as a ZIP file or copy the repository URL to clone it using Git.

3.	Extract the ZIP File (if applicable):
-	If you downloaded the ZIP file, extract its contents to a directory of your choice.

4.	Open a Terminal or Command Prompt:
- Open a terminal or command prompt on your system.

5.	Navigate to the Weather App Directory:
-	With the `cd` command, navigate to the directory where you extracted the Weather app source code or cloned the repository.

6.	Install Dependencies:
-	Run the following command to install the required dependencies:
  ```
  pip install -r requirements.txt
  ```

7.	Obtain a Weatherbit API Key:
-	Visit the Weatherbit website at https://www.weatherbit.io and sign up for a free account.
-	After signing in, navigate to your account dashboard and obtain your API key.

8. Configure the API Key:
- In the Weather app source code directory, locate the `configuration.py` file.
- Open the `configuration.py` file in a text editor and replace the placeholder value for `API_KEY` with your Weatherbit API key.
- Save the changes.

## Usage
To verify that the Weather app is correctly installed and configured, follow these steps:
1.	In the terminal or command prompt, navigate to the Weather app directory.
2.	Run the following command to start the Weather app:
    ````
    python weather_app.py
    ```
3.	Follow the prompts
4.	The app should then retrieve and display the weather information for the specified city in your desired units, including temperature, humidity, wind speed, and description.

If you see the weather information displayed correctly, congratulations! The Weather app is successfully installed and configured on your system.

## Conclusion
Thank you for checking out this app! Check back for more features and code improvements.