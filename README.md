# BlackBucks - A Cryptocurrency with BlockChain Implemenations

> BlackBucks is an experimental digital currency that enables instant payments to anyone, anywhere in the world.
> BlackBucks uses peer-to-peer technology to operate with no central authority: managing transactions and issuing
> money is carried out collectively by the network. BlackBucks also includes a Web-based Wallet named the BlackCard.
> BlackBucks started as a project at Hampton University.

## Software Requirements

+ Python3.6+
+ PIP for Python

## Python Installation

1. Download and install the latest version of Python
 [Currently 3.6.5](https://www.python.org/downloads/)
2. Run the installer and check the option to set your [environment variables](https://msdn.microsoft.com/en-us/library/windows/desktop/ms682653(v=vs.85).aspx)
3. Be sure to install PIP in the Python Installer

    + If you forget to install PIP, you can find install instructions [here](https://www.makeuseof.com/tag/install-pip-for-python/)

4. After PIP is installed, run the following command in a terminal

    > `pip install pipenv && pipenv --python==python3.6`

5. You can install all required packages by running

    > `pipenv install`

## Configuring the Project

1. Navigate to the project folder, For example
    > `\home\user\Project\BlackBucks`

2. The user configuration file is located in the `\config\user.yaml` folder

3. The public_key_file and private_key_file variables should be set to the absolute file path of your public and private key files. For example:
    > `\home\user\Project\BlackBucks\YourPrivateKey.pem`

## Running the project

1. To run the project, navigate to the project folder. For example,
    > `\home\user\Project\BlackBucks`

2. Open a terminal window.

3. In the terminal, run the following command
    > `python BlockChain.py <ip_address>`
    > This will start the program on the given IP Address

4. Open your browser of choice, and navigate to the address (<ip_address>:5000).

> From here you should be greeted to a main page and
> should be able to send and recieve BlackBucks as well
> as add new nodes and view the full BlockChain.