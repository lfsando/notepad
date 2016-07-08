#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    This file is part of Notepad.
    
    Notepad is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import sys
import functools
import datetime

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import highlighter


class Filter(QtCore.QObject):

    def __init__(self):
        super().__init__()
        self.count = 0

    def eventFilter(self, widget, event):

        if event.type() == QtCore.QEvent.FocusOut:
            if not widget.hasFocus():
                blur = QtWidgets.QGraphicsBlurEffect()
                blur.setBlurRadius(2)
                widget.setGraphicsEffect(blur)
            return False
        else:
            if widget.hasFocus():
                widget.setGraphicsEffect(None)
            return False


class Notepad(QtWidgets.QMainWindow):
    # INIT
    def __init__(self, window_width=1000, window_height=950):
        super().__init__()

        # Initialize Plain Text Widget

        self.text_widget = QtWidgets.QPlainTextEdit()

        # Default Mode to Insertion

        self.insert = True

        # EventFilter FocusOut

        self._filter = Filter()

        # Setup Shortcuts

        self.shift_tab = QtWidgets.QShortcut(QtGui.QKeySequence('Shift+Tab'), self)
        #self.shift_tab.activated.setFocus()

        # Default start up File

        self.file_name = 'Untitled.txt'
        self.file_path = ['/', '']
        self.file_type = self.file_name.split('.')[-1]
        self.syntax = highlighter.PythonHighlighter(self.text_widget.document())
        self.assign_syntax_def()

        # Initialize Menus

        self.menu_bar = self.menuBar()
        self.file_menu()
        self.edit_menu()
        self.format_menu()
        self.preferences_menu()
        self.finder_toolbar()

        # Set Default Pallete

        self.default_visual()

        # Initialize UI Related Properties

        self.notepad_ui()

        self.setCentralWidget(self.text_widget)
        self.setWindowIcon(QtGui.QIcon('assets/icons/notepad.png'))
        self.resize(window_width, window_height)

        # Center the main window to the screen
        self.center()
        self.show()

    def notepad_ui(self):

        self.update_cursor()
        self.update_statusbar()
        self.need_saving(False)

        self.new_file()
        self.finder_focus()
        self.setWindowTitle('{} - Notepad'.format(self.file_name))

        self.text_widget.textChanged.connect(functools.partial(self.need_saving, True))
        self.text_widget.textChanged.connect(self.update_statusbar)
        self.text_widget.textChanged.connect(self.search_text, True)
        self.text_widget.cursorPositionChanged.connect(self.update_statusbar)

    def new_file(self):
        '''Open a new file'''

        if self.has_changed:
            has_saved = self.save_box(new=True)
        else:
            has_saved = True

        if has_saved:
            self.text_widget.clear()
            self.file_path = './'
            self.file_name = 'Untitled'
            self.setWindowTitle("{} - Notepad".format(self.file_name))
            self.need_saving(False)

    def center(self):
        """Center the window"""

        frame = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())

    # EVENTS

    def keyPressEvent(self, event):

        if event.key() == QtCore.Qt.Key_Insert:
            if self.text_widget.overwriteMode():
                self.text_widget.setOverwriteMode(False)
                self.insert = True
                self.update_statusbar()
            else:
                self.text_widget.setOverwriteMode(True)
                self.insert = False
                self.update_statusbar()

        if event.key() == QtCore.Qt.Key_Return:
            self.search_text(True)

    # DEFAULT VISUALS AND STATUS BAR

    def closeEvent(self, event):
        if self.has_changed:
            save_ = QtWidgets.QMessageBox()
            save_.setIcon(QtWidgets.QMessageBox.Question)
            save_.setWindowTitle('Save and Exit')
            save_.setText('The document has been modified.')
            save_.setInformativeText('Do you want to save your changes?')
            save_.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard |
                                     QtWidgets.QMessageBox.Cancel)
            save_.setDefaultButton(QtWidgets.QMessageBox.Save)
            save_.setEscapeButton(QtWidgets.QMessageBox.Cancel)
            reply = save_.exec_()

            # reply returns an int
            # Save
            if reply == 2048:
                self.save_file()
                event.accept()
            # Discard
            elif reply == 8388608:
                event.accept()
            # Cancel
            else:
                event.ignore()
        else:
            event.accept()

    # DEFAULT VISUALS, STATUSBAR AND SYNTAX

    def default_visual(self):

        # Pallete
        default_palette = self.text_widget.palette()

        # Background
        default_background_color = QtGui.QColor()
        default_background_color.setNamedColor('#2B2B2B')
        default_palette.setColor(QtGui.QPalette.Base, default_background_color)

        # Font Color
        default_font_color = QtGui.QColor()
        default_font_color.setNamedColor('#F8F8F2')
        default_palette.setColor(QtGui.QPalette.Text, default_font_color)

        # Font Type
        default_font = QtGui.QFont('Consolas', 13)
        self.text_widget.setFont(default_font)

        self.text_widget.setPalette(default_palette)

    def default_format(self):
        self.default_visual()

    def assign_syntax_def(self):
        self.syntax.setDocument(None)
        self.update_statusbar()

    def assign_syntax_py(self):
        self.syntax = PythonHighlighter(self.text_widget.document())
        self.update_statusbar()

    def get_cursor_position(self):
        """ Get Row and Column of actual text cursor """
        self.update_cursor()
        cursor_row = self.text_cursor.blockNumber() + 1
        cursor_column = self.text_cursor.columnNumber()
        return cursor_row, cursor_column

    def update_cursor(self):
        """ Update Text Cursor """
        self.text_cursor = self.text_widget.textCursor()
        self.text_widget.setTextCursor(self.text_cursor)

    def update_statusbar(self):
        """ Update the status bar with information"""
        cursor_row, cursor_column = self.get_cursor_position()
        newline_count = self.text_widget.blockCount()
        char_count = self.char_count()
        lines_str = 'lines: ' + str(newline_count)
        chars_str = '  |  chars: ' + str(char_count)
        column_str = '  |  Col: ' + str(cursor_column)
        row_str = '  |  Row: ' + str(cursor_row)
        ins_str = '  |  INS'
        ovr_string = '  |  OVR'

        status_string = lines_str + chars_str + column_str + row_str
        status_lbl = QtWidgets.QLabel(status_string)
        status_lbl.setAlignment(QtCore.Qt.AlignLeft)

        filepath_lbl = QtWidgets.QLabel(str(self.file_path[0]))
        filepath_lbl.setToolTip(str(self.file_path[0]))
        filepath_lbl.setAlignment(QtCore.Qt.AlignLeft)

        syntax_lbl = QtWidgets.QLabel()
        syntax_lbl.setAlignment(QtCore.Qt.AlignCenter)

        if self.syntax:
            syntax_lbl.setText('Python')
        else:
            syntax_lbl.setText('Default')

        custom_status = QtWidgets.QStatusBar()
        custom_status.addWidget(filepath_lbl, stretch=2)
        custom_status.addWidget(status_lbl, stretch=1)
        custom_status.addWidget(syntax_lbl, stretch=0)
        custom_status.adjustSize()

        self.setStatusBar(custom_status)

        if self.insert:
            status_lbl.setText(status_string + ins_str)
        else:
            status_lbl.setText(status_string + ovr_string)

    # MENU

    def char_count(self):

        content = self.text_widget.toPlainText()
        content_chars = list(content)
        char_count = len(content_chars)
        return char_count

    def file_menu(self):
        """ Create a file menu in the menubar """

        file_menu = self.menu_bar.addMenu('&File')

        # New File Action
        new_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/new.png'), '&New File', self)
        new_action.setStatusTip('Start a new file')
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)

        # Open a File Action
        open_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/open.png'), '&Open...', self)
        open_action.setStatusTip('Open a file')
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_dialog)

        # Save a File Action
        save_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/save.png'), '&Save', self)
        save_action.setStatusTip('Save a file')
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)

        # Save File as Action
        save_as_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/save_as.png'), 'Save &As', self)
        save_as_action.setStatusTip('Save as.. a file')
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_dialog)

        # Exit
        exit_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/exit.png'), '&Exit', self)
        exit_action.setStatusTip('Exit')
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(QtWidgets.qApp.quit)

        # Add actions to menu

        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

    def edit_menu(self):

        edit_menu = self.menu_bar.addMenu('&Edit')

        undo_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/undo.png'), '&Undo Typing', self)
        undo_action.setStatusTip('Undo last action')
        undo_action.setShortcut('Ctrl+Z')
        undo_action.triggered.connect(self.undo_action)

        cut_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/cut.png'), 'Cu&t', self)
        cut_action.setStatusTip('Cut the selection to clipboard')
        cut_action.setShortcut('Ctrl+X')
        cut_action.triggered.connect(self.cut_action)

        copy_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/copy.png'), '&Copy', self)
        copy_action.setStatusTip('Copy selection to clipboard')
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(self.copy_action)

        paste_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/paste.png'), '&Paste', self)
        paste_action.setStatusTip('Paste from clipboard')
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(self.paste_action)

        del_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/del.png'), '&Delete', self)
        del_action.setStatusTip('Delete selection')
        del_action.setShortcut('Del')
        del_action.triggered.connect(self.del_action)

        find_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/find.png'), '&Find', self)
        find_action.setStatusTip('Find a string')
        find_action.setShortcut('Ctrl+F')
        find_action.triggered.connect(self.find_action)

        find_next_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/find_next.png'), 'Find &next', self)
        find_next_action.setStatusTip('Find next string in file')
        find_next_action.setShortcut('Ctrl+Shift+F')
        find_next_action.triggered.connect(self.find_next_action)

        goto_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/go_to.png'), '&Go to...', self)
        goto_action.setStatusTip('Go to line')
        goto_action.setShortcut('Ctrl+G')
        goto_action.triggered.connect(functools.partial(self.goto_action, default=''))

        select_all_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/select_all.png'), '&Select All', self)
        select_all_action.setStatusTip('Select all lines')
        select_all_action.setShortcut('Ctrl+A')
        select_all_action.triggered.connect(self.select_all_action)

        edit_menu.addAction(undo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(cut_action)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)
        edit_menu.addAction(del_action)
        edit_menu.addSeparator()
        edit_menu.addAction(find_action)
        edit_menu.addAction(find_next_action)
        edit_menu.addAction(goto_action)
        edit_menu.addSeparator()
        edit_menu.addAction(select_all_action)

    def preferences_menu(self):
        
        settings_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/config.png'), '&Settings', self)
        settings_action.setStatusTip('Open Settings')
        settings_action.setShortcut('Ctrl+Shift+P')

        preferences_menu = self.menu_bar.addMenu('Prefere&nces')
        preferences_menu.addAction(settings_action)


    def format_menu(self):
        """ Add Format Menu """

        font_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/font.png'), '&Font', self)
        font_action.setStatusTip('Change the document font')
        font_action.triggered.connect(self.font_dialog)

        date_action = QtWidgets.QAction(QtGui.QIcon('assets/icons/date.png'), '&Append Date', self)
        date_action.setStatusTip('Insert date and time at cursor location')
        date_action.setShortcut('F5')
        date_action.triggered.connect(self.insert_date)

        self.default_syntax = QtWidgets.QAction('&Default', self)
        self.default_syntax.setStatusTip('Turn off syntax highlighting')

        self.python_syntax = QtWidgets.QAction('&Python', self)
        self.python_syntax.setStatusTip('Turn on syntax highlighting for Python language')

        self.default_syntax.triggered.connect(self.assign_syntax_def)
        self.python_syntax.triggered.connect(self.assign_syntax_py)

        format_menu = self.menu_bar.addMenu('Forma&t')

        syntax_menu = format_menu.addMenu(QtGui.QIcon('assets/icons/synthax.png'), '&Syntax')

        syntax_menu.addAction(self.default_syntax)
        syntax_menu.addAction(self.python_syntax)

        format_menu.addSeparator()
        format_menu.addAction(font_action)
        format_menu.addAction(date_action)

    # Text Finder

    def finder_toolbar(self):

        self.finder_toolbar = QtWidgets.QToolBar()
        self.finder_toolbar.setAllowedAreas(QtCore.Qt.TopToolBarArea)
        self.finder_toolbar.setHidden(True)
        self.finder_toolbar.setFloatable(True)
        self.finder_tool()
        self.finder_toolbar.addWidget(self.finder)

        btn_close = QtWidgets.QToolButton()
        btn_close.setIcon(QtGui.QIcon('assets/icons/close.png'))
        btn_close.setFixedSize(16, 16)
        btn_close.clicked.connect(self.finder_toolbar.hide)

        self.finder_toolbar.addWidget(btn_close)
        self.addToolBar(self.finder_toolbar)
        self.finder_focus()

    def finder_tool(self):

        self.finder = QtWidgets.QLineEdit()
        self.finder.setPlaceholderText('Find...')
        self.finder.textChanged.connect(self.search_text)

        self.finder_focus()

    def finder_focus(self):
        self.finder.installEventFilter(self._filter)

    def search_text(self, jump_to_next=False):
        _input = self.finder.text()
        text = self.text_widget.toPlainText()
        input_length = len(_input)
        results = []

        # if there's text in the search box and it's not hidden
        if _input and not self.finder_toolbar.isHidden():
            for nth in range(len(text)):
                # if the nth letter in the text matches with the first letter in the input
                if text[nth] == _input[0]:
                    # if the nth word which has the length of the input length matches the input
                    if str(text[nth:nth + input_length]) == _input:
                        # append start position and last position to results
                        results.append((nth, nth + input_length))
        else:
            pass
        if results:
            self.highlight_matches(results)


    def highlight_matches(self, results):
        print(results)
        pass
        #class Match()
        #selected = QtGui.QTextCharFormat()



    # ACTIONS

    def index_count(self, count):
        return count + 1

    def find_action(self):

        if self.finder_toolbar.isHidden():
            self.finder_toolbar.setHidden(False)

        if not self.finder_toolbar.isHidden():
            self.finder.setFocus(QtCore.Qt.ShortcutFocusReason)

    def undo_action(self):
        self.text_widget.undo()

    def cut_action(self):
        self.text_widget.cut()

    def copy_action(self):
        self.text_widget.copy()

    def paste_action(self):
        self.text_widget.paste()

    def del_action(self):
        self.update_cursor()
        self.text_cursor.deleteChar()

    def find_next_action(self):
        pass

    def goto_action(self, default):

        try:
            line, ok = QtWidgets.QInputDialog.getText(self, "Go to..", "Go to line:", text=str(default))

            if ok:
                self.update_cursor()
                if line.isdecimal and (int(line) >= 1) and (int(line) <= self.text_widget.blockCount()):

                    current_line = self.text_cursor.blockNumber() + 1
                    moves = int(line) - current_line

                    if moves < 0:
                        self.text_cursor.movePosition(QtGui.QTextCursor.Up, QtGui.QTextCursor.KeepAnchor, -moves);
                        self.text_widget.setTextCursor(self.text_cursor)
                    else:
                        self.text_cursor.movePosition(QtGui.QTextCursor.Down, QtGui.QTextCursor.MoveAnchor, moves)
                        self.text_widget.setTextCursor(self.text_cursor)

                    self.text_cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                    self.text_widget.setTextCursor(self.text_cursor)

                else:
                    default = line
                    raise ValueError

        except ValueError:
            self.goto_action(default=line)

    def select_all_action(self):

        self.text_widget.selectAll()

    def insert_date(self):

        today = self.get_datetime()
        self.text_widget.insertPlainText(today)

    # DIALOGS

    @staticmethod
    def get_datetime():

        date = datetime.datetime.today().strftime('%d/%m/%Y %H:%M:%S')
        return date

    def font_dialog(self):
        """ Change Font dialog """

        font, ok = QtWidgets.QFontDialog.getFont(self)

        if ok:
            self.text_widget.setFont(font)

    def need_saving(self, check_):
        """ Check if file needs to be saved"""

        self.has_changed = check_

        if self.has_changed:
            self.setWindowTitle('{}* - Notepad'.format(self.file_name))
        else:
            self.setWindowTitle('{} - Notepad'.format(self.file_name))

    def open_dialog(self):
        """ Open 'Open Dialog Box' """

        if self.has_changed:
            self.save_box(open=True)

        try:
            self.file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', './',
                                                         filter="All Files(*.*);;Text Files(*.txt)")

            if self.file_path[0]:
                self.file_name = (self.file_path[0].split('/'))[-1]

                self.setWindowTitle("{} - Notepad".format(self.file_name))

                file_open = open(self.file_path[0], 'r+')
                self.statusBar().showMessage('Open... {}'.format(self.file_path[0]))

                with file_open:
                    content = file_open.read()
                    self.text_widget.setPlainText(content)
                    self.need_saving(False)


        except UnicodeDecodeError as why:
            self.error_box(why)
            pass

    def save_box(self, new=False, open=False):
        """Save Message Box"""

        reply = QtWidgets.QMessageBox().question(self, 'Notepad', "Do you want to save {}".format(self.file_name),
                                                 QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.No |
                                                 QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Save)
        if reply == QtWidgets.QMessageBox.Save:
            self.save_file()
            if new:
                return True

        elif reply == QtWidgets.QMessageBox.No:
            if new:
                return True

        elif reply == QtWidgets.QMessageBox.Cancel:
            if new:
                return False
            elif open:
                pass

    def save_dialog(self):

        try:
            save_dialog = QtWidgets.QFileDialog()
            save_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            file_path = save_dialog.getSaveFileName(self, 'Save as... File', './',
                                                    filter='All Files(*.*);; Text Files(*.txt)')

            if file_path[0]:
                self.file_path = file_path
                file_open = open(self.file_path[0], 'w')
                self.file_name = (self.file_path[0].split('/'))[-1]
                self.statusBar().showMessage('Saved at: {}'.format(self.file_path[0]))
                self.setWindowTitle("{} - Notepad".format(self.file_name))
                with file_open:
                    file_open.write(self.text_widget.toPlainText())
                    self.need_saving(False)

        except FileNotFoundError as why:
            self.error_box(why)
            pass

    def save_file(self):

        try:
            if self.file_path:
                if (self.file_path[0].split('/')[-1].lower()) == self.file_name.lower():
                    file_open = open(self.file_path[0], 'w')
                    self.file_name = (self.file_path[0].split('/'))[-1]
                    self.setStatusTip('Saved at: {}'.format(self.file_path[0]))
                    self.setWindowTitle("{} - Notepad".format(self.file_name))
                    with file_open:
                        file_open.write(self.text_widget.toPlainText())
                        self.need_saving(False)
                    return
                else:
                    self.save_dialog()

        except FileNotFoundError as why:
            self.error_box(why)

    @staticmethod
    def error_box(why):
        """Open Error Box with exception"""

        error_message = QtWidgets.QMessageBox()
        error_message.setWindowTitle('Error !')
        error_message.setIcon(QtWidgets.QMessageBox.Critical)
        error_message.setText('An error was found.')
        error_message.setInformativeText('%s' % why)
        error_message.exec_()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    notes = Notepad()
    sys.exit(app.exec_())
