# -*- coding: utf-8 -*-

# Snippet source
# https://github.com/cstrap/python-snippets
# https://realpython.com/primer-on-python-decorators/#functions
# https://realpython.com/python-logging/

import os
import re
from json import load

import pyzo
from pyzo.util.qt import QtCore, QtGui, QtWidgets
from pyzo import translate

tool_name = translate('pyzoSnippetManager', 'Snippet Manager')
tool_summary = "Shows the structure of your source code."


class PyzoSnippetManager(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        # Make sure there is a configuration entry for this tool
        # The pyzo tool manager makes sure that there is an entry in
        # config.tools before the tool is instantiated.
        toolId = self.__class__.__name__.lower()
        self._config = pyzo.config.tools[toolId]
        if not hasattr(self._config, 'showTypes'):
            self._config.showTypes = ['class', 'def', 'cell', 'todo']
        if not hasattr(self._config, 'level'):
            self._config.level = 2

        # Keep track of sorting order
        self._sort_order = None

        # Snippet folder
        self.snippet_folder = os.path.join(pyzo.appDataDir, 'tools', 'pyzoSnippetManager', 'snippets')

        # Create button for reload
        self._reload = QtWidgets.QToolButton(self)
        self._reload.setIcon(pyzo.icons.arrow_refresh)
        self._reload.setToolTip("Reload")
        # event
        self._reload.clicked.connect(self.onReloadPress)

        # Create button for sorting
        self._sortbut = QtWidgets.QToolButton(self)
        self._sortbut.setToolButtonStyle (QtCore.Qt.ToolButtonTextBesideIcon)
        self._sortbut.setArrowType(QtCore.Qt.DownArrow)
        self._sortbut.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        self._sortbut.setText('A-z')
        self._sortbut.setToolTip("Sorted")
        # event
        self._sortbut.clicked.connect(self.onSortPress)

        # Create button ofor opening snippet file in the editor
        self._open_file = QtWidgets.QToolButton(self)
        self._open_file.setIcon(pyzo.icons.page_white_text)
        self._open_file.setIconSize(QtCore.QSize(16,16))
        self._open_file.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        self._open_file.setToolTip("Open snippet file")
        # event
        self._open_file.clicked.connect(self.onOpenFile)

        # Create options button
        # self._options = QtWidgets.QToolButton(self)
        # self._options.setIcon(pyzo.icons.filter)
        # self._options.setIconSize(QtCore.QSize(16,16))
        # self._options.setPopupMode(self._options.InstantPopup)
        # self._options.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # Create options menu
        # self._options._menu = QtWidgets.QMenu()
        # self._options.setMenu(self._options._menu)

        # Create tree widget
        self._tree = QtWidgets.QTreeWidget(self)
        self._tree.setColumnCount(2)
        self._tree.setHeaderLabels(["description", "prefix"])
        self._tree.setColumnWidth(0, 350)
        self._tree.setHeaderHidden(True)
        self._tree.setSortingEnabled(True)
        self._tree.sortItems(0, QtCore.Qt.AscendingOrder)

        # Create two sizers
        self._sizer1 = QtWidgets.QVBoxLayout(self)
        self._sizer2 = QtWidgets.QHBoxLayout()
        self._sizer1.setSpacing(2)
        self._sizer1.setContentsMargins(0, 0, 0, 0)

        # Set layout
        self._sizer1.addLayout(self._sizer2, 0)
        self._sizer1.addWidget(self._tree, 1)
        # self._sizer2.addWidget(self._sliderIcon, 0)
        self._sizer2.addWidget(self._reload, 0)
        self._sizer2.addWidget(self._sortbut, 0)
        self._sizer2.addStretch(1)
        self._sizer2.addWidget(self._open_file, 0)
        # self._sizer2.addWidget(self._navbut_forward, 0)
        # self._sizer2.addStretch(1)
        # self._sizer2.addWidget(self._slider, 6)
        # self._sizer2.addStretch(1)
        # self._sizer2.addWidget(self._options, 0)
        #
        self.setLayout(self._sizer1)

        # Init current-file name
        self._currentEditorId = 0

        self.fillTree()

        # Bind to events
        self._tree.clicked.connect(self.onItemClicked)

    def fillTree(self):
        # fill tree
        self._snippet = {}
        self._part = {}
        for f in os.listdir(self.snippet_folder):
            # print('\nF -------------------: ' + str(f))
            root = f.replace('.json', '').title()
            sf = os.path.join(self.snippet_folder, f)
            with open(sf) as snippet:
                self._part[root] = load(snippet)
                self._snippet.update(self._part)
                root = QtWidgets.QTreeWidgetItem(self._tree, [root])
                for k, v in self._part.items():
                    for kk, vv in v.items():
                        # print('V: ' + str(v))
                        QtWidgets.QTreeWidgetItem(root, [str(kk), str(vv['prefix'])])
                self._part.clear()
        self._tree.sortItems(0, QtCore.Qt.AscendingOrder)
        self._sort_order = 'ASC'
        self._sortbut.setText('A-z')
        self._sortbut.setArrowType(QtCore.Qt.DownArrow)

    def _insertSnippet(self, body):

        if isinstance(body, list):
            txt = ''
            for i, t in enumerate(body):
                txt = body[i] + '\n'
            body = txt

        body = body.replace('\t', '    ')
        body = body.replace('$0', '')

        # Find patern ${num : text}
        # TODO: nested pattern ${2: ${3:Exception} as ${4:e}}
        d = {}
        pattern = '\$\{\d.*?}'
        match = re.findall(pattern, body)
        for fnd in match:
            fnd_split = fnd.split(':')
            # key
            key = fnd_split[0]
            key = key.replace('{', '')
            body = body.replace(fnd, key)
            # value
            value = fnd_split[1]
            value = value.replace('}', '')
            # dict
            d[key] = value

        # In snippet replace keys with values
        for i in reversed(range(10)):
            try:
                i = "$" + str(i)
                body = body.replace(i, d[i])
            except:
                pass

        # Write in the editor
        editor = pyzo.editors.getCurrentEditor()
        # cursor
        cursor = editor.textCursor()
        # current position
        pos = cursor.position()
        # insert the snippet
        cursor.insertText(body)

        # Find target text in the editor
        text = editor.toPlainText()
        pattern = '$1'

        if pattern in d:
            # find text
            regex = QtCore.QRegExp(d[pattern])
            index = regex.indexIn(text, pos)
            # select text
            cursor.setPosition(index)
            cursor.movePosition(QtGui.QTextCursor.EndOfWord, 1)
            editor.setTextCursor(cursor)

    def onItemClicked(self):
        """ onItemClicked()
        If item clicked in the workspace tree insert snippet
        """
        item = self._tree.currentItem()

        try:
            parent = item.parent()
            parent_val = self._tree.indexFromItem(parent, 0).data()
            code = self._snippet[parent_val][item.text(0)]['body']
            self._insertSnippet(code)
        except:
            pass

    # def onOptionsPress(self):
    #     """ Create the menu for the button, Do each time to make sure
    #     the checks are right. """
    #
    #     # Get menu
    #     menu = self._options._menu
    #     menu.clear()
    #
    #     for type in ['class', 'def', 'cell', 'todo', 'import', 'attribute']:
    #         checked = type in self._config.showTypes
    #         action = menu.addAction('Show %s'%type)
    #         action.setCheckable(True)
    #         action.setChecked(checked)
    #
    # def onOptionMenuTiggered(self, action):
    #     """  The user decides what to show in the structure. """
    #
    #     # What to show
    #     type = action.text().split(' ',1)[1]

   ##       # Swap
    #     if type in self._config.showTypes:
    #         while type in self._config.showTypes:
    #             self._config.showTypes.remove(type)
    #     else:
    #         self._config.showTypes.append(type)

    def onReloadPress(self):
        self._tree.clear()
        self.fillTree()

    def onSortPress(self):
        """ Sort the tree alphabetically. """

        self._tree.setSortingEnabled(True)

        if self._sort_order in [None, 'DSC']:
            self._tree.sortItems(0, QtCore.Qt.AscendingOrder)
            self._sort_order = 'ASC'
            self._sortbut.setText('A-z')
            self._sortbut.setArrowType(QtCore.Qt.DownArrow)

        elif self._sort_order == 'ASC':
            self._tree.sortItems(0, QtCore.Qt.DescendingOrder)
            self._sort_order = 'DSC'
            self._sortbut.setText('Z-a')
            self._sortbut.setArrowType(QtCore.Qt.UpArrow)

    def onOpenFile(self):

        try:
            item = self._tree.currentItem().text(0)
        except:
            return

        fname = '{}.json'.format(item.lower())
        fpath = os.path.join(self.snippet_folder, fname)
        pyzo.editors.loadFile(fpath)