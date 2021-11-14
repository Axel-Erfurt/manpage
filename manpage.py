# /usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_versions({'Gtk': '3.0', 'Gdk': '3.0'})
from gi.repository import Gtk, Gdk, Gio
import os
from subprocess import check_output

CSS = """
window {
    background: #c9c9c9;
}
textview text {
    background: #e6e6e6;
}
entry {
    font-size: 8pt;
    margin-top: 10px;
    margin-bottom: 10px;
    background: #d9d9d9;
}
searchentry {
    font-size: 8pt;
    margin-top: 10px;
    margin-bottom: 10px;
    background: #eeeeec;
}
headerbar {
    font-size: 11pt;
    min-height: 28px;
    padding-left: 2px;
    padding-right: 2px;
    margin: 0px;
    padding: 5px;
    border: 0px;
    background: #c9c9c9;
}
headerbar entry,
headerbar button,
headerbar separator {
    font-size: 8pt;
    margin-top: 0px;
    margin-bottom: 0px;
    padding: 1px;
}
statusbar {
    font-size: 8pt;
    color: #444;
    background: #c9c9c9;
    margin: 0px;
}
"""

class ManViewer(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        
        self.set_title("ManViewer")
        self.set_icon_name("applications-utilities")
        self.set_default_size(750, 800)
        self.set_border_width(10)
        self.connect("destroy", Gtk.main_quit)
        
        self.cmd_folder = "cmd_man"

        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "Manuals"
        hb.props.subtitle = "Terminal Befehle"
        self.set_titlebar(hb)
        
        # style
        provider = Gtk.CssProvider()
        provider.load_from_data(bytes(CSS.encode()))
        style = self.get_style_context()
        screen = Gdk.Screen.get_default()
        priority = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        style.add_provider_for_screen(screen, provider, priority)
        
        btn_style_up = Gtk.Image.new_from_gicon(Gio.ThemedIcon(name="down"), Gtk.IconSize.MENU)
        self.cmd_combo = Gtk.MenuButton(label="Manuals  ", image=btn_style_up)
        self.cmd_combo.props.relief = 2
        self.cmd_menu = Gtk.Menu()
        self.cmd_combo.set_popup(self.cmd_menu) 
        hb.pack_start(self.cmd_combo)
        
        self.find_field = Gtk.SearchEntry(placeholder_text="im Text suchen", tooltip_text="im Text suchen")
        self.find_field.connect("activate", self.find_text)
        self.find_field.connect("search_changed", self.on_search_changed)
                                   
        save_button = Gtk.Button(tooltip_text = "speichern")
        save_button.props.relief = 2
        save_button.connect("clicked", self.save_cmd)
        icon = Gio.ThemedIcon(name="document-save")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.SMALL_TOOLBAR)
        save_button.add(image)
        hb.pack_end(save_button)
        
        self.cmd_field = Gtk.Entry(placeholder_text="Befehl eingeben -> ENTER", tooltip_text="Befehl eingeben -> ENTER")
        self.cmd_field.connect("activate", self.run_cmd)
        hb.pack_end(self.cmd_field)
        
        self.buffer = Gtk.TextBuffer()
        self.cmd_viewer = Gtk.TextView(vexpand=True, hexpand=True, left_margin=10)
        
        ### tags for search color
        self.tag_found = self.buffer.create_tag("found", background="#edd400")
        
        self.scrollview = Gtk.ScrolledWindow()
        self.scrollview.add(self.cmd_viewer)
        
        self.statusbar = Gtk.Statusbar.new()
        
        hbox = Gtk.HBox()
        vbox = Gtk.VBox()
        vbox.add(self.scrollview)
        hbox.pack_start(self.find_field, False, False, 2)
        vbox.pack_start(hbox, False, False, 2)
        vbox.pack_end(self.statusbar, False, False, 0)
        self.add(vbox)
        
        self.statusbar.push(0, "Manuals")
        
        self.fill_combo()
        self.cmd_field.grab_focus()
        
    def fill_combo(self, *args):
        for i in self.cmd_menu.get_children():
            self.cmd_menu.remove(i)
        cmd_list = []
        for root, dirs, files in os.walk(self.cmd_folder, topdown = False):
           for name in files:
              if name.endswith(".txt"):
                #print(os.path.join(root, name))
                cmd_list.append(name.replace(".txt", ""))
        cmd_list.sort(key=str.lower)
        for cmd_file in cmd_list:
            menuitem = Gtk.MenuItem(label = cmd_file)
            menuitem.connect("activate", self.on_cmd_activated)
            self.cmd_menu.append(menuitem)
        self.cmd_menu.show_all()
        
    def on_cmd_activated(self, menuitem, *args):
        cmd_file = f"cmd_man/{menuitem.get_label()}.txt"       
        with open(cmd_file, 'r') as f:
            data = f.read()
            self.buffer.set_text(data)
            self.cmd_viewer.set_buffer(self.buffer)
            self.statusbar.push(0, f"{menuitem.get_label()} geladen")

    def run_cmd(self, *args):
        cmd = self.cmd_field.get_text()
        if len(cmd) > 1:
            try:
                data = check_output(f"man {cmd}", shell = True).decode()
                self.buffer.set_text(data)
                self.cmd_viewer.set_buffer(self.buffer)
            except:
                self.buffer.set_text("")
                self.statusbar.push(0, "kein Handbucheintrag vorhanden!")
        else:
            print("kein Befehl")
            self.statusbar.push(0, "kein Befehl eingegeben!")
            
    ### get editor text
    def get_buffer(self):
        start_iter = self.buffer.get_start_iter()
        end_iter = self.buffer.get_end_iter()
        text = self.buffer.get_text(start_iter, end_iter, True) 
        return text
            
    def save_cmd(self, *args):
        text = self.get_buffer()
        cmd = self.cmd_field.get_text()
        if len(cmd) > 1 and text != "":
            cmd_file = f"cmd_man/{cmd}.txt"
            with open(cmd_file, 'w') as f:
                f.write(text)
                f.close()
            self.fill_combo()
        else:
            self.statusbar.push(0, "kein Befehl eingegeben oder kein Handbucheintrag vorhanden!")

                
    ### find all occurences in editor and select
    def on_search_changed(self, widget):
        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        self.buffer.remove_all_tags(start, end)
        self.find_text()
        
    def find_text(self, *args):
        search_text = self.find_field.get_text()
        if not search_text == "":
            start = self.buffer.get_start_iter() ###get_iter_at_mark(cursor_mark)
            if start.get_offset() == self.buffer.get_char_count():
                start = self.buffer.get_start_iter()

            self.search_and_mark(search_text, start)

    ### mark matches
    def search_and_mark(self, text, start):
        end = self.buffer.get_end_iter()
        match = start.forward_search(text, 0, end)

        if match is not None:
            match_start, match_end = match
            self.buffer.apply_tag(self.tag_found, match_start, match_end)
            self.search_and_mark(text, match_end)

window = ManViewer()
window.show_all()
window.move(0, 0)

Gtk.main()