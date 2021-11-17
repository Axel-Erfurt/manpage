# /usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_versions({'Gtk': '3.0'})
from gi.repository import Gtk, Gio
import os
from subprocess import check_output
import string

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
        
            # alle befehle
        if os.path.isfile("Liste.txt"):
            btn_style_up = Gtk.Image.new_from_gicon(Gio.ThemedIcon(name="down"), Gtk.IconSize.MENU)
            self.list_combo = Gtk.MenuButton(label="Manuals a-z ", image=btn_style_up)
            self.list_combo.props.relief = 2
            
            menu = Gtk.Menu()
            self.list_combo.set_popup(menu) 
        
            befehlsliste = open("Liste.txt", "r").read().splitlines()
            letters = list(string.ascii_lowercase)
            for x in range(len(letters)):
                item = Gtk.MenuItem(label=letters[x])
                menu.append(item)
                sub_menu = Gtk.Menu()
                
                for befehl in befehlsliste:
                    if befehl.startswith(letters[x]):
                        befehl = befehl.split(" ")[0]
                        menuitem = Gtk.MenuItem(label=befehl)
                        menuitem.connect("activate", self.on_menuitem_activated)
                        sub_menu.append(menuitem)
                
                item.set_submenu(sub_menu)

            # numbers
            item = Gtk.MenuItem(label="1-9")
            menu.append(item)
            sub_menu = Gtk.Menu()
            for befehl in befehlsliste:
                first = befehl[:1]
                if first.isnumeric():
                    befehl = befehl.split(" ")[0]
                    if befehl != "":
                        menuitem = Gtk.MenuItem(label=befehl)
                        menuitem.connect("activate", self.on_menuitem_activated)
                        sub_menu.append(menuitem)
            item.set_submenu(sub_menu)
            
            
            menu.show_all()
        
            hb.pack_start(self.list_combo)
            
            # entry completion
            self.liststore = Gtk.ListStore(str)
            self.completion = Gtk.EntryCompletion()
            self.completion.set_model(self.liststore)
            self.completion.set_text_column(0)
            
            for befehl in befehlsliste:
                befehl = befehl.split(" ")[0]
                self.liststore.append([befehl])  
            
            self.cmd_field.set_completion(self.completion)
            self.completion.complete()  
            self.completion.set_text_column(0)
            self.completion.set_minimum_key_length(1)
            
            self.completion.set_match_func(self.match_func, None)
            self.completion.connect("match-selected", self.on_completion_match)
        
        self.buffer = Gtk.TextBuffer()
        self.cmd_viewer = Gtk.TextView(vexpand=True, hexpand=True, left_margin=10, editable=False)
        
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
        
    def match_func(self, completion, key_string, iter, data):
        model = self.completion.get_model()
        modelstr = model[iter][0]

        if " " in key_string:
            last_word = key_string.split()[-1]
            return modelstr.startswith(last_word)

        return modelstr.startswith(key_string)

    def on_completion_match(self, completion, model, iter):
        current_text = self.cmd_field.get_text()
        
        if " " in current_text:
            current_text = " ".join(current_text.split()[:-1])
            current_text = "%s %s" % (current_text, model[iter][0])
        else:
            current_text = model[iter][0]

        current_text = model[iter][0]
        self.cmd_field.set_text(current_text)
        self.run_cmd()
        return True
        
    def on_menuitem_activated(self, menuitem, *args):      
        cmd = menuitem.get_label()
        self.cmd_field.set_text(cmd)
        self.run_cmd()
        self.statusbar.push(0, f"{cmd} geladen")

        
    def fill_combo(self, *args):
        for i in self.cmd_menu.get_children():
            self.cmd_menu.remove(i)
        cmd_list = []
        for root, dirs, files in os.walk(self.cmd_folder, topdown = False):
           for name in files:
              if name.endswith(".txt"):
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
            self.cmd_field.set_text("")

    def run_cmd(self, *args):
        cmd = self.cmd_field.get_text()
        if len(cmd) > 1:
            try:
                self.cmd_viewer.grab_focus()
                data = check_output(f"man {cmd}", shell = True).decode()
                self.buffer.set_text(data)
                self.cmd_viewer.set_buffer(self.buffer)
                start_iter = self.buffer.get_start_iter()
                self.buffer.place_cursor(start_iter)
                self.cmd_viewer.scroll_to_iter(start_iter, 0.0, True, 0.0, 0.0)
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
