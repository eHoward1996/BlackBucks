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

## Running the project

> To run the project, navigate to the project folder. For example,
>
> `\home\user\Project\BlackBucks`
>
> and open a terminal window. In the terminal, run the following command
>
> `python BlockChain.py -p <port_number>`
>
> This will start the program on port number <port_number>
---
> Open your browser of choice, and navigate to
> your localhost address (localhost:5000).
> From here you should be greeted to a login page and
> should be able to enter credentials and use the wallet.