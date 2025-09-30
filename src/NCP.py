
# python -m PyInstaller --onefile --uac-admin --icon=NCP.ico NCP.py

import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import subprocess
import json
from json import JSONDecodeError
from tkinter import filedialog
import hashlib

root = tk.Tk()

RUNNABLE_EXTS = (
    '.exe', '.exe1', '.dll', '.com', '.bat', '.cmd', '.msi', '.msp', '.msu',
    '.msc', '.mst', '.bin', '.app', '.ins', '.isu', '.paf',     # binaries / installers / updates
    '.scr', '.pif', '.inf1', '.shb', '.shs',                                                      # screensaver / program info
    '.lnk', '.scf', '.inf', '.job', '.jse', '.lnk', '.ps1', '.sct', '.u3p',                                             # shortcuts / shell command / setup scripts
    '.cpl', '.msc',                                                       # control panel / MMC snap-in
    '.ocx', '.sys', '.drv',                                               # components / drivers
    '.reg', '.rgs',                                                               # registry import
    '.jar',                                                                # Java
    '.ps1', '.psm1', '.psd1', '.ps1xml',                                   # PowerShell
    '.vbs', '.vbe', '.js', '.jse', '.vb', 'vbscript',                                        # VBScript / JScript
    '.wsf', '.wsh', '.wsc', '.ws',                                         # Windows Script Host & components
    '.hta', '.gadget',                                                     # HTML applications / gadgets
    '.py', '.pyw',                                                          # Python
    '.pl', '.pm',                                                           # Perl (scripts / modules)
    '.rb',                                                                  # Ruby
    '.php',                                                                 # PHP scripts (if PHP interpreter present)
    '.sh', '.shb', '.sct',                                                                # shell scripts (WSL/Cygwin/GitBash)
    '.ps1xml',                                                              # powershell xml
)


toggle_vars_in = []
toggle_vars_out = []
checkbox_frame = tk.Frame(root)
checkbox_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")

def delete_firewall_rules():
    """
    Deletes all Windows Firewall rules whose names start with '[Network_Control_Panel'.
    Only rules with this prefix are targeted and removed.
    """
    try:
        # Get all rules
        result = subprocess.run('netsh advfirewall firewall show rule name=all', shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            # netsh may write errors to stdout/stderr; show whichever is present
            err = (result.stderr or result.stdout).strip()
            print(f"Failed to list firewall rules: {err}")
            return

        for line in result.stdout.splitlines():
            line_str = line.strip()
            # lines look like: "Rule Name:    [Network_Control_Panel(in)]Block_xxx"
            if line_str.startswith("Rule Name:") and "[Network_Control_Panel" in line_str:
                # extract the part after the first ':' and strip any padding
                parts = line_str.split(':', 1)
                if len(parts) < 2:
                    continue
                rule_name = parts[1].strip()
                cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if proc.returncode == 0:
                    print(f"Deleted firewall rule: {rule_name}")
                else:
                    output = (proc.stdout or proc.stderr).strip()
                    print(f"Failed to delete rule {rule_name}: {output}")
    except Exception as e:
        messagebox.showerror("Error", f"Error deleting firewall rules: {e}")

def clear_all_data():
    try:
        """Clears all entries from data.json after confirming with the user."""
        if not os.path.exists("data.json"):
            messagebox.showinfo("No Data", "data.json does not exist, nothing to clear.")
            return

        confirm = messagebox.askyesno(
            "Confirm Clear",
            "Are you sure you want to clear all data? This cannot be undone."
        )
        if not confirm:
            return
        
        delete_firewall_rules()  # Delete all related firewall rules

        # Clear the JSON file
        with open("data.json", "w") as f:
            json.dump({"blocked_dangerousfiles": []}, f, indent=2)

        messagebox.showinfo("Data Cleared", "All data has been cleared.")
        refresh_checkboxes()  # Refresh the UI checkboxes
    except Exception as e:
        messagebox.showerror("Error", f"Error clearing data: {e}")

clear_btn = tk.Button(root, text="Clear All Data", command=clear_all_data,)
clear_btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")

def safe_rule_name(dfile_path):
    filename = os.path.basename(dfile_path)  # just the file name
    short_hash = hashlib.md5(dfile_path.encode()).hexdigest()[:6]
    return f"{filename}_{short_hash}"

def delete_entry(program_index):
    with open("data.json", "r") as f:
        data = json.load(f)
    program = data["blocked_dangerousfiles"][program_index]
    folder = program["folder_to_block"]
    dangerousfiles = program["dangerousfiles"]

    # Remove firewall rules for each dangerousfile
    for dfile in dangerousfiles:
        dfile_path = os.path.join(folder, dfile)
        dfile_path = dfile_path.replace("\\\\", "\\")
        dfile_path = dfile_path.replace("/", "\\")
        name = safe_rule_name(dfile_path)
        cmd = f'netsh advfirewall firewall delete rule name="[Network_Control_Panel(in)]Block_{name}"'
        cmd2 = f'netsh advfirewall firewall delete rule name="[Network_Control_Panel(out)]Block_{name}"'
        try:
            subprocess.run(cmd, shell=True, check=True)
            subprocess.run(cmd2, shell=True, check=True)
            print(f"Deleted firewall rule for {dfile_path}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to delete rule for {dfile_path}:\n{e}")

    # Remove the entry from the JSON data
    del data["blocked_dangerousfiles"][program_index]
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"Deleted entry for folder: {folder}")

    # Refresh the checkboxes
    refresh_checkboxes()

# def shrink_to_fit(win):
#     # recompute layout
#     win.update_idletasks()
#     # requested size for all widgets
#     req_w = win.winfo_reqwidth()
#     req_h = win.winfo_reqheight()
#     # current actual window size
#     cur_w = win.winfo_width()
#     cur_h = win.winfo_height()
#     # only shrink (don't expand) to avoid fighting user's manual resize
#     if req_w < cur_w or req_h < cur_h:
#         win.geometry(f"{req_w}x{req_h}")

def refresh_checkboxes():
    # Clear any existing checkboxes
    for widget in checkbox_frame.winfo_children():
        widget.destroy()

    try:
        with open("data.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        data = {"blocked_dangerousfiles": []}

    toggle_vars_in.clear()
    toggle_vars_out.clear()

    try:

        for idx, program in enumerate(data["blocked_dangerousfiles"]):
            folder_to_block = program.get("folder_to_block", "(unknown)")
            is_blocked_in = program.get("is_blocked_in", False)
            is_blocked_out = program.get("is_blocked_out", False)

            toggle_var_in = tk.BooleanVar(value=is_blocked_in)
            toggle_vars_in.append(toggle_var_in)
            toggle_var_out = tk.BooleanVar(value=is_blocked_out)
            toggle_vars_out.append(toggle_var_out)

            folder_label = tk.Label(checkbox_frame, text=folder_to_block)
            folder_label.grid(row=idx+3, column=0, sticky="w", padx=5, pady=2)

            delete_btn = tk.Button(checkbox_frame, text="Delete", command=lambda idx=idx: delete_entry(idx))
            delete_btn.grid(row=idx+3, column=1, padx=5, pady=2, sticky="w")

            inbound = tk.Checkbutton(checkbox_frame, text="Inbound", variable=toggle_var_in,
                                     command=lambda idx=idx, var_in=toggle_var_in, var_out=None: toggle_dfilec(idx, var_in, var_out))
            inbound.grid(row=idx+3, column=2, padx=5, pady=2, sticky="w")
            outbound = tk.Checkbutton(checkbox_frame, text="Outbound", variable=toggle_var_out,
                                      command=lambda idx=idx, var_in=None, var_out=toggle_var_out: toggle_dfilec(idx, var_in, var_out))
            outbound.grid(row=idx+3, column=3, padx=5, pady=2, sticky="w")

        # shrink_to_fit(root)
    except Exception as e:
        messagebox.showerror("Error", f"Error loading checkboxes: {e}.")

refresh_checkboxes()

def save_blocked_folder(folder_to_block, dangerousfiles):
    file_path = "data.json"

    # Prepare new entry
    new_entry = {
        "folder_to_block": folder_to_block,
        "is_blocked_outbound": False,
        "is_blocked_inbound": False,
        "dangerousfiles": dangerousfiles
    }

    # Load existing data
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {"blocked_dangerousfiles": []}
    else:
        data = {"blocked_dangerousfiles": []}

    # Check for duplicates based on folder path
    folders = [entry["folder_to_block"] for entry in data["blocked_dangerousfiles"]]
    if folder_to_block in folders:
        print(f"Folder '{folder_to_block}' is already in data.json - skipping.")
        return

    # Append new folder
    data["blocked_dangerousfiles"].append(new_entry)

    # Write updated data back
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {folder_to_block} with {len(dangerousfiles)} dangerousfiles to data.json")

# Function to run a system command
def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Ran: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {command}: {e}")

def add_block_rule(folder_to_block):
    # Defensive: ensure we got a folder path
    print(f"add_block_rule called with: '{folder_to_block}'")
    if not folder_to_block:
        messagebox.showerror("Invalid Path", "No folder path provided. Please select a folder.")
        return
    dangerousfiles = []
    print(f"Scanning folder tree starting at: {folder_to_block}")
    for root, dirs, files in os.walk(folder_to_block):
        print(f"Visiting: {root} (contains {len(files)} files, {len(dirs)} dirs)")
        for file in files:
            # show each file considered (optional, can be noisy)
            # print(f"Considering file: {file}")
            if file.lower().endswith(RUNNABLE_EXTS):
                print(f"Considering file: {file}")
                dfile_path = os.path.join(root, file)
                dfile_path = dfile_path.replace("\\\\", "\\")
                print(f"Found dangerousfile: {dfile_path}")
                dangerousfiles.append(dfile_path)
        
    if len(dangerousfiles) == 0:
        messagebox.showinfo(
           "No dangerousfiles Found",
           f"No files found in '{folder_to_block}'.\n\nPlease check the folder path or select a different folder."
       )
        return

    # Create outbound firewall rules to block each file
    for dfile in dangerousfiles:
        dfile = dfile.replace("\\\\", "\\")
        dfile = dfile.replace("/", "\\")
        dfile = safe_rule_name(dfile)
        cmd = f'netsh advfirewall firewall add rule name="[Network_Control_Panel(out)]Block_{dfile}" dir=out program="{dfile}" action=block'
        cmd2 = f'netsh advfirewall firewall set rule name="[Network_Control_Panel(out)]Block_{dfile}" new enable=no'

        cmd3 = f'netsh advfirewall firewall add rule name="[Network_Control_Panel(in)]Block_{dfile}" dir=in program="{dfile}" action=block'
        cmd4 = f'netsh advfirewall firewall set rule name="[Network_Control_Panel(in)]Block_{dfile}" new enable=no'

        run_command(cmd)
        run_command(cmd2)
        run_command(cmd3)
        run_command(cmd4)

    save_blocked_folder(folder_to_block, dangerousfiles)

    refresh_checkboxes()  # Refresh the checkboxes to show the new entry
    
    print(f"Blocked {len(dangerousfiles)} files in {folder_to_block}")
    if len(dangerousfiles) > 0:
        print("Blocked items:")
        for e in dangerousfiles:
            print(f" - {e}")

def process_input():
    # Get the text from the Entry widget
    print("Processing input...") 
    user_text = entry.get()
    print(f"User entered: {user_text}")
    # You can now pass it to any function
    add_block_rule(user_text)
    # Nothing to see here
    
# Function to block/unblock dangerousfiles
def toggle_dfilec(program_index, toggle_var_in=None, toggle_var_out=None):
    with open("data.json", "r") as f:
        data = json.load(f)
    program = data["blocked_dangerousfiles"][program_index]
    folder = program["folder_to_block"]
    dangerousfiles = program["dangerousfiles"]
    
    if toggle_var_in is not None:
        actionin = "yes" if toggle_var_in.get() else "no" # "yes" to enable (block), "no" to disable (unblock)
    if toggle_var_out is not None:
        actionout = "yes" if toggle_var_out.get() else "no" # "yes" to enable (block), "no" to disable (unblock)

    # Update the JSON data
    if toggle_var_in is not None:
        program["is_blocked_in"] = toggle_var_in.get()
    if toggle_var_out is not None:
        program["is_blocked_out"] = toggle_var_out.get()
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)
        
    for dfile in dangerousfiles:
        dfile_path = os.path.join(folder, dfile)
        print(f"dfilepath {dfile_path}")
        dfile_path = dfile_path.replace("\\\\", "\\")
        dfile_path = dfile_path.replace("/", "\\")
        name = safe_rule_name(dfile_path)
        try:
            if toggle_var_in is not None:
                cmd1 = f'netsh advfirewall firewall set rule name="[Network_Control_Panel(in)]Block_{name}" new enable={actionin}'
                subprocess.run(cmd1, shell=True, check=True)
            if toggle_var_out is not None:
                cmd2 = f'netsh advfirewall firewall set rule name="[Network_Control_Panel(out)]Block_{name}" new enable={actionout}'
                subprocess.run(cmd2, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            if toggle_var_in is not None:
                messagebox.showerror("Error", f"Failed to (yes = block, no = unblock) for inbound {actionin} {dfile_path}:\n{e}")
            if toggle_var_out is not None:
                messagebox.showerror("Error", f"Failed to (yes = block, no = unblock) for outbound {actionout} {dfile_path}:\n{e}")




root.title("Network Control Panel")

# Label explaining the input
label = tk.Label(root, text="Enter folder path to block its files from transmitting over the Internet (DON'T use or close the application while it is loading, more info in bundled doc):", wraplength=300, justify="left")
label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")

# Entry widget for folder path
entry = tk.Entry(root, width=50)
entry.grid(row=1, column=0, padx=10, pady=5, sticky="w")

def browse_folder():
    folder_selected = filedialog.askdirectory(title="Select Folder")
    if folder_selected:
        print(f"User selected folder: {folder_selected}")
        # Put the selected folder into the Entry first, then process it.
        entry.delete(0, tk.END)
        entry.insert(0, folder_selected)
        process_input()  # Process the input immediately after selection



# Button to submit
file_btn = tk.Button(root, text="Select Folder", command=browse_folder)


file_btn.grid(row=1, column=1, padx=10)

refresh_checkboxes()

root.mainloop()