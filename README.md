## Network Control Panel

This is a frontend for Windows Firewall with Advanced Security that also supports blocking entire folders, which the firewall itself doesn't.
The executable is located under src. Keep in mind it requires admin privileges since it modifies firewall rules.

The source code and related files can also be found here. The executable is standalone, AS LONG AS YOU INCLUDE THE DATA.JSON, meaning you can take it out of this folder (with the data.json).

Use discretion and do not select a folder with too many files.

The inbound checkbox allows you to block data coming in from the internet to that folder. The outbound checkbox allows you to block it from sending data over the internet. This is all done via Windows Firewall, and thus will only work for Windows.

To block a folder, click select folder and select the folder. The path should pop up, with two checkboxes and a delete button.

If an unresolvable issue occurs, open Network Control Panel and click Clear All Data. This should have deleted the firewall rules also, but double check by opening Windows Firewall with Advanced Security and make sure there are no rules (in inbound or outbound) starting with "[Network_Control_Panel". Alternatively, you can manually cut the JSON file and the firewall rules to not delete everything, but be careful.

## Installation

I have provided complied executables for you, but they may trigger antiviruses. If you want to compile the Python code directly from source (so you can read the code), do the following:

1. Make sure you have pyinstaller installed. Run "pip install pyinstaller" if not
2. Compile the code. If you want the terminal to show, use "python -m PyInstaller --onefile --windowed --uac-admin --icon=NCP.ico NCP.py" If you want it hidden, use "python -m PyInstaller --onefile --uac-admin --icon=NCP.ico NCP.py"

## Use Cases

Use anytime you want to block a folder from having internet access. If you have a program you think is selling your data, take steps to prevent it by blocking the program folder. Just be careful, if internet is absolutely essential, you might want to re-enable internet before using.

Licensed under MIT




