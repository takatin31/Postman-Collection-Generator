import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
from pathlib import Path

class PostmanGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Postman Collection Generator")
        self.root.geometry("800x600")
        
        # Store selected paths
        self.input_paths = []
        self.client_paths = []  # New list for directly selected client folders
        self.output_path = ""
        
        # Create main container with padding
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Postman Collection Generator", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # First tab - Root directories
        root_tab = ttk.Frame(notebook, padding=10)
        notebook.add(root_tab, text="Root Directories")
        
        # Second tab - Client directories
        client_tab = ttk.Frame(notebook, padding=10)
        notebook.add(client_tab, text="Client Folders")
        
        # --- Root Directories Tab ---
        # Paths listbox with scrollbar
        root_paths_frame = ttk.Frame(root_tab)
        root_paths_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.root_paths_listbox = tk.Listbox(root_paths_frame, height=10)
        self.root_paths_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        root_scrollbar = ttk.Scrollbar(root_paths_frame, orient=tk.VERTICAL, command=self.root_paths_listbox.yview)
        root_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.root_paths_listbox.config(yscrollcommand=root_scrollbar.set)
        
        # Buttons for managing root paths
        root_paths_button_frame = ttk.Frame(root_tab)
        root_paths_button_frame.pack(fill=tk.X, pady=5)
        
        add_root_button = ttk.Button(root_paths_button_frame, text="Add Root Directory", 
                                     command=self.add_input_path)
        add_root_button.pack(side=tk.LEFT, padx=5)
        
        remove_root_button = ttk.Button(root_paths_button_frame, text="Remove Selected", 
                                       command=self.remove_input_path)
        remove_root_button.pack(side=tk.LEFT, padx=5)
        
        clear_root_button = ttk.Button(root_paths_button_frame, text="Clear All", 
                                      command=self.clear_input_paths)
        clear_root_button.pack(side=tk.LEFT, padx=5)
        
        # --- Client Folders Tab ---
        # Client paths listbox with scrollbar
        client_paths_frame = ttk.Frame(client_tab)
        client_paths_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.client_paths_listbox = tk.Listbox(client_paths_frame, height=10)
        self.client_paths_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        client_scrollbar = ttk.Scrollbar(client_paths_frame, orient=tk.VERTICAL, command=self.client_paths_listbox.yview)
        client_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.client_paths_listbox.config(yscrollcommand=client_scrollbar.set)
        
        # Buttons for managing client paths
        client_paths_button_frame = ttk.Frame(client_tab)
        client_paths_button_frame.pack(fill=tk.X, pady=5)
        
        add_client_button = ttk.Button(client_paths_button_frame, text="Add Client Folder", 
                                      command=self.add_client_path)
        add_client_button.pack(side=tk.LEFT, padx=5)
        
        remove_client_button = ttk.Button(client_paths_button_frame, text="Remove Selected", 
                                         command=self.remove_client_path)
        remove_client_button.pack(side=tk.LEFT, padx=5)
        
        clear_client_button = ttk.Button(client_paths_button_frame, text="Clear All", 
                                        command=self.clear_client_paths)
        clear_client_button.pack(side=tk.LEFT, padx=5)
        
        # Help text
        help_client = ttk.Label(client_tab, text="Select folders that end with '-client' directly")
        help_client.pack(pady=5)
        
        # Output directory section
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="10")
        output_frame.pack(fill=tk.X, pady=10)
        
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=60)
        output_entry.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.X, expand=True)
        
        output_button = ttk.Button(output_frame, text="Browse...", command=self.select_output_path)
        output_button.pack(side=tk.RIGHT, padx=5, pady=10)
        
        # Status section
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        status_label = ttk.Label(status_frame, text="Status:")
        status_label.pack(side=tk.LEFT, padx=5)
        
        status_value = ttk.Label(status_frame, textvariable=self.status_var)
        status_value.pack(side=tk.LEFT, padx=5)
        
        # Generate button
        generate_button = ttk.Button(main_frame, text="Generate Postman Collections", 
                                     command=self.generate_collections)
        generate_button.pack(pady=20)
        
    def add_input_path(self):
        directory = filedialog.askdirectory(title="Select Root Directory")
        if directory:
            if directory not in self.input_paths:
                self.input_paths.append(directory)
                self.root_paths_listbox.insert(tk.END, directory)
                self.status_var.set(f"Added root directory: {directory}")
            else:
                messagebox.showinfo("Duplicate", "This directory is already in the list.")
    
    def remove_input_path(self):
        try:
            selected_idx = self.root_paths_listbox.curselection()[0]
            path = self.root_paths_listbox.get(selected_idx)
            self.root_paths_listbox.delete(selected_idx)
            self.input_paths.remove(path)
            self.status_var.set(f"Removed root directory: {path}")
        except (IndexError, ValueError):
            messagebox.showinfo("Selection Error", "Please select a directory to remove.")
    
    def clear_input_paths(self):
        self.root_paths_listbox.delete(0, tk.END)
        self.input_paths = []
        self.status_var.set("Cleared all root directories")
    
    def add_client_path(self):
        directory = filedialog.askdirectory(title="Select Client Folder")
        if directory:
            # Check if the selected directory ends with '-client'
            if not os.path.basename(directory).endswith('-client'):
                if not messagebox.askyesno("Warning", 
                                          f"The selected folder '{os.path.basename(directory)}' does not end with '-client'.\n\nDo you want to add it anyway?"):
                    return
            
            if directory not in self.client_paths:
                self.client_paths.append(directory)
                self.client_paths_listbox.insert(tk.END, directory)
                self.status_var.set(f"Added client folder: {directory}")
            else:
                messagebox.showinfo("Duplicate", "This client folder is already in the list.")
    
    def remove_client_path(self):
        try:
            selected_idx = self.client_paths_listbox.curselection()[0]
            path = self.client_paths_listbox.get(selected_idx)
            self.client_paths_listbox.delete(selected_idx)
            self.client_paths.remove(path)
            self.status_var.set(f"Removed client folder: {path}")
        except (IndexError, ValueError):
            messagebox.showinfo("Selection Error", "Please select a client folder to remove.")
    
    def clear_client_paths(self):
        self.client_paths_listbox.delete(0, tk.END)
        self.client_paths = []
        self.status_var.set("Cleared all client folders")
    
    def select_output_path(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_path = directory
            self.output_var.set(directory)
            self.status_var.set(f"Output directory set to: {directory}")
    
    def generate_collections(self):
        all_paths = self.input_paths + self.client_paths
        
        if not all_paths:
            messagebox.showerror("Error", "Please add at least one root directory or client folder.")
            return
        
        if not self.output_path:
            messagebox.showerror("Error", "Please select an output directory.")
            return
        
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Assume the main script is in the same directory and named "postman_generator.py"
        main_script = os.path.join(script_dir, "postman_generator.py")
        
        if not os.path.exists(main_script):
            messagebox.showerror("Error", f"Cannot find the generator script at {main_script}")
            return
        
        # Build the command
        cmd = [sys.executable, main_script] + all_paths + ["--output", self.output_path]
        
        self.status_var.set("Generating collections...")
        self.root.update()
        
        try:
            # Run the command
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.status_var.set("Collections generated successfully!")
                messagebox.showinfo("Success", "Postman collections have been generated successfully.\n\n" + 
                                   f"Output directory: {self.output_path}")
                
                # Ask if user wants to open the output directory
                if messagebox.askyesno("Open Directory", "Do you want to open the output directory?"):
                    self.open_output_directory()
            else:
                self.status_var.set("Error generating collections.")
                messagebox.showerror("Error", f"Error generating collections:\n\n{stderr}")
        except Exception as e:
            self.status_var.set("Error running generator.")
            messagebox.showerror("Error", f"Error running the generator:\n\n{str(e)}")
    
    def open_output_directory(self):
        try:
            if sys.platform == 'win32':
                os.startfile(self.output_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', self.output_path])
            else:  # Linux
                subprocess.run(['xdg-open', self.output_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open the directory: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PostmanGeneratorApp(root)
    root.mainloop()