import json
import os
import sys

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivateIgnoringOtherApps,
    NSApplicationActivationPolicyRegular,
    NSBezelStyleRounded,
    NSButton,
    NSColor,
    NSDragOperationCopy,
    NSFont,
    NSMakeRect,
    NSMenu,
    NSMenuItem,
    NSOpenPanel,
    NSPasteboardTypeFileURL,
    NSRunningApplication,
    NSScrollView,
    NSSplitView,
    NSTableColumn,
    NSTableView,
    NSTableViewSelectionHighlightStyleNone,
    NSTextField,
    NSFilenamesPboardType,
    NSFocusRingTypeNone,
    NSLineBreakByTruncatingTail,
    NSView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSIndexSet, NSObject, NSURL
from WebKit import WKWebView, WKWebViewConfiguration, WKWebsiteDataStore

from html_renderer import render_markdown_html


WINDOW_WIDTH = 1220
WINDOW_HEIGHT = 780
SIDEBAR_WIDTH = 290
PADDING = 18
SIDEBAR_PADDING = 12
SIDEBAR_LIST_LEFT_OFFSET = 6
PATH_BAR_HEIGHT = 34
TOC_BUTTON_SIZE = 34
TOC_PANEL_WIDTH = 260
TOC_PANEL_MAX_HEIGHT = 320


def rgb(red: int, green: int, blue: int):
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(red / 255.0, green / 255.0, blue / 255.0, 1.0)


def make_label(frame, text: str, font, color, background=False):
    label = NSTextField.alloc().initWithFrame_(frame)
    label.setBezeled_(False)
    label.setDrawsBackground_(background)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setStringValue_(text)
    label.setFont_(font)
    label.setTextColor_(color)
    return label


def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class DropContentView(NSView):
    def initWithFrame_owner_(self, frame, owner):
        self = objc.super(DropContentView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.owner = owner
        self.registerForDraggedTypes_([NSFilenamesPboardType, NSPasteboardTypeFileURL])
        return self

    def draggingEntered_(self, sender):
        if self.owner._extract_markdown_path(sender.draggingPasteboard()):
            return NSDragOperationCopy
        return 0

    def prepareForDragOperation_(self, sender):
        return self.owner._extract_markdown_path(sender.draggingPasteboard()) is not None

    def performDragOperation_(self, sender):
        return self.owner._load_pasteboard_files(sender.draggingPasteboard())


class DropSplitView(NSSplitView):
    def initWithFrame_owner_(self, frame, owner):
        self = objc.super(DropSplitView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.owner = owner
        self.registerForDraggedTypes_([NSFilenamesPboardType, NSPasteboardTypeFileURL])
        return self

    def draggingEntered_(self, sender):
        if self.owner._extract_markdown_path(sender.draggingPasteboard()):
            return NSDragOperationCopy
        return 0

    def prepareForDragOperation_(self, sender):
        return self.owner._extract_markdown_path(sender.draggingPasteboard()) is not None

    def performDragOperation_(self, sender):
        return self.owner._load_pasteboard_files(sender.draggingPasteboard())


class DropTableView(NSTableView):
    def initWithFrame_owner_(self, frame, owner):
        self = objc.super(DropTableView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.owner = owner
        self.registerForDraggedTypes_([NSFilenamesPboardType, NSPasteboardTypeFileURL])
        return self

    def draggingEntered_(self, sender):
        if self.owner._extract_markdown_path(sender.draggingPasteboard()):
            return NSDragOperationCopy
        return 0

    def prepareForDragOperation_(self, sender):
        return self.owner._extract_markdown_path(sender.draggingPasteboard()) is not None

    def performDragOperation_(self, sender):
        return self.owner._load_pasteboard_files(sender.draggingPasteboard())

    def mouseDown_(self, event):
        click_point = self.convertPoint_fromView_(event.locationInWindow(), None)
        row = self.rowAtPoint_(click_point)
        column = self.columnAtPoint_(click_point)
        if self == getattr(self.owner, "file_table_view", None) and row >= 0 and column >= 0:
            table_column = self.tableColumns()[column]
            if table_column == getattr(self.owner, "file_delete_column", None):
                self.owner.remove_opened_file_at_row(row)
                return
        objc.super(DropTableView, self).mouseDown_(event)


class DropScrollView(NSScrollView):
    def initWithFrame_owner_(self, frame, owner):
        self = objc.super(DropScrollView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.owner = owner
        self.registerForDraggedTypes_([NSFilenamesPboardType, NSPasteboardTypeFileURL])
        return self

    def draggingEntered_(self, sender):
        if self.owner._extract_markdown_path(sender.draggingPasteboard()):
            return NSDragOperationCopy
        return 0

    def prepareForDragOperation_(self, sender):
        return self.owner._extract_markdown_path(sender.draggingPasteboard()) is not None

    def performDragOperation_(self, sender):
        return self.owner._load_pasteboard_files(sender.draggingPasteboard())


class DropOverlayView(NSView):
    def initWithFrame_owner_(self, frame, owner):
        self = objc.super(DropOverlayView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.owner = owner
        self.registerForDraggedTypes_([NSFilenamesPboardType, NSPasteboardTypeFileURL])
        self.setWantsLayer_(True)
        self.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
        return self

    def hitTest_(self, _point):
        return None

    def draggingEntered_(self, sender):
        if self.owner._extract_markdown_path(sender.draggingPasteboard()):
            return NSDragOperationCopy
        return 0

    def prepareForDragOperation_(self, sender):
        return self.owner._extract_markdown_path(sender.draggingPasteboard()) is not None

    def performDragOperation_(self, sender):
        return self.owner._load_pasteboard_files(sender.draggingPasteboard())


class TocDismissOverlayView(NSView):
    def initWithFrame_owner_(self, frame, owner):
        self = objc.super(TocDismissOverlayView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.owner = owner
        self.setWantsLayer_(True)
        self.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
        self.registerForDraggedTypes_([NSFilenamesPboardType, NSPasteboardTypeFileURL])
        return self

    def mouseDown_(self, _event):
        self.owner._set_toc_panel_visible(False)

    def draggingEntered_(self, sender):
        if self.owner._extract_markdown_path(sender.draggingPasteboard()):
            return NSDragOperationCopy
        return 0

    def prepareForDragOperation_(self, sender):
        return self.owner._extract_markdown_path(sender.draggingPasteboard()) is not None

    def performDragOperation_(self, sender):
        return self.owner._load_pasteboard_files(sender.draggingPasteboard())


class DropWebView(WKWebView):
    def initWithFrame_configuration_owner_(self, frame, configuration, owner):
        self = objc.super(DropWebView, self).initWithFrame_configuration_(frame, configuration)
        if self is None:
            return None
        self.owner = owner
        self.registerForDraggedTypes_([NSFilenamesPboardType, NSPasteboardTypeFileURL])
        return self

    def draggingEntered_(self, sender):
        if self.owner._extract_markdown_path(sender.draggingPasteboard()):
            return NSDragOperationCopy
        return 0

    def prepareForDragOperation_(self, sender):
        return self.owner._extract_markdown_path(sender.draggingPasteboard()) is not None

    def performDragOperation_(self, sender):
        return self.owner._load_pasteboard_files(sender.draggingPasteboard())


class DropWindow(NSWindow):
    def setOwner_(self, owner):
        self.owner = owner
        self.registerForDraggedTypes_([NSFilenamesPboardType, NSPasteboardTypeFileURL])

    def draggingEntered_(self, sender):
        if self.owner._extract_markdown_path(sender.draggingPasteboard()):
            return NSDragOperationCopy
        return 0

    def prepareForDragOperation_(self, sender):
        return self.owner._extract_markdown_path(sender.draggingPasteboard()) is not None

    def performDragOperation_(self, sender):
        return self.owner._load_pasteboard_files(sender.draggingPasteboard())


class MarkdownAppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, _notification):
        self.current_file = None
        self.opened_files = []
        self.heading_targets = []
        self.toc_panel_visible = False
        self._build_main_menu()
        self._build_window()
        self.window.makeKeyAndOrderFront_(None)
        NSRunningApplication.currentApplication().activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        self.show_placeholder()
        self.open_file_on_startup()

    def applicationShouldTerminateAfterLastWindowClosed_(self, _app):
        return True

    def application_openFile_(self, _app, filename):
        markdown_path = self._normalize_markdown_path(filename)
        if not markdown_path:
            return False
        self.load_file(markdown_path)
        return True

    def application_openFiles_(self, app, filenames):
        if self.load_files(filenames):
            app.replyToOpenOrPrint_(0)
            return
        app.replyToOpenOrPrint_(1)

    def numberOfRowsInTableView_(self, _table_view):
        if _table_view == self.file_table_view:
            return len(self.opened_files)
        return len(self.heading_targets)

    def tableView_objectValueForTableColumn_row_(self, _table_view, _column, row):
        if _table_view == self.file_table_view:
            if row >= len(self.opened_files):
                return ""
            if _column == self.file_delete_column:
                return "x"
            return os.path.basename(self.opened_files[row])
        if row >= len(self.heading_targets):
            return ""
        level, title, _anchor = self.heading_targets[row]
        return "%s%s" % ("  " * max(level - 1, 0), title)

    def tableView_toolTipForCell_rect_tableColumn_row_mouseLocation_(self, table_view, _cell, rect, _table_column, row, _mouse_location):
        if table_view == self.file_table_view and 0 <= row < len(self.opened_files):
            return os.path.basename(self.opened_files[row])
        return None

    def tableView_willDisplayCell_forTableColumn_row_(self, table_view, cell, _table_column, row):
        if table_view != self.file_table_view or not 0 <= row < len(self.opened_files):
            return
        if _table_column == self.file_delete_column:
            cell.setTitle_("x")
            cell.setFont_(NSFont.systemFontOfSize_(11))
            cell.setTextColor_(rgb(120, 128, 140))
            return
        file_name = os.path.basename(self.opened_files[row])
        is_current = self.opened_files[row] == self.current_file
        cell.setTitle_(file_name)
        cell.setFont_(NSFont.boldSystemFontOfSize_(14) if is_current else NSFont.systemFontOfSize_(14))
        cell.setTextColor_(rgb(36, 41, 47))

    def tableView_shouldEditTableColumn_row_(self, table_view, _table_column, _row):
        return False

    def tableViewSelectionDidChange_(self, notification):
        table_view = notification.object()
        row = table_view.selectedRow()
        if table_view == self.file_table_view:
            if 0 <= row < len(self.opened_files):
                selected_path = self.opened_files[row]
                if selected_path != self.current_file:
                    self.load_file(selected_path)
            return
        if 0 <= row < len(self.heading_targets):
            _level, _title, anchor = self.heading_targets[row]
            script = "scrollToHeading(%s);" % json.dumps(anchor)
            self.web_view.evaluateJavaScript_completionHandler_(script, None)

    def chooseFile_(self, _sender):
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(False)
        panel.setAllowsMultipleSelection_(True)
        panel.setAllowedFileTypes_(["md", "markdown"])
        panel.setTitle_("选择 Markdown 文件")
        if panel.runModal() == 1:
            file_paths = []
            for url in panel.URLs() or []:
                if url:
                    file_paths.append(url.path())
            if not file_paths:
                url = panel.URL()
                if url:
                    file_paths.append(url.path())
            self.load_files(file_paths)

    def closeCurrentFile_(self, _sender):
        if not self.current_file:
            self.window.performClose_(None)
            return
        try:
            row = self.opened_files.index(self.current_file)
        except ValueError:
            self.window.performClose_(None)
            return
        self.remove_opened_file_at_row(row)

    def clearFileList_(self, _sender):
        self.clear_opened_files()

    def windowDidResize_(self, _notification):
        self._layout_views()

    def splitViewDidResizeSubviews_(self, _notification):
        self._layout_split_content()

    def toggleTocPanel_(self, _sender):
        self._set_toc_panel_visible(not self.toc_panel_visible)

    def _build_main_menu(self):
        main_menu = NSMenu.alloc().init()

        app_menu_item = NSMenuItem.alloc().init()
        main_menu.addItem_(app_menu_item)
        app_menu = NSMenu.alloc().initWithTitle_("Markdown Parser")
        app_menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("关于 Markdown Parser", "orderFrontStandardAboutPanel:", ""))
        app_menu.addItem_(NSMenuItem.separatorItem())
        app_menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("隐藏 Markdown Parser", "hide:", "h"))
        app_menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("隐藏其他", "hideOtherApplications:", "h"))
        app_menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("显示全部", "unhideAllApplications:", ""))
        app_menu.addItem_(NSMenuItem.separatorItem())
        app_menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("退出 Markdown Parser", "terminate:", "q"))
        main_menu.setSubmenu_forItem_(app_menu, app_menu_item)

        file_menu_item = NSMenuItem.alloc().init()
        main_menu.addItem_(file_menu_item)
        file_menu = NSMenu.alloc().initWithTitle_("文件")
        file_menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("打开...", "chooseFile:", "o"))
        file_menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("关闭当前文件", "closeCurrentFile:", "w"))
        file_menu.addItem_(NSMenuItem.separatorItem())
        file_menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("清空文件列表", "clearFileList:", ""))
        main_menu.setSubmenu_forItem_(file_menu, file_menu_item)

        edit_menu_item = NSMenuItem.alloc().init()
        main_menu.addItem_(edit_menu_item)
        edit_menu = NSMenu.alloc().initWithTitle_("编辑")
        edit_menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("复制", "copy:", "c"))
        edit_menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("全选", "selectAll:", "a"))
        main_menu.setSubmenu_forItem_(edit_menu, edit_menu_item)

        NSApplication.sharedApplication().setMainMenu_(main_menu)

    def _build_window(self):
        style = (
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskResizable
            | NSWindowStyleMaskMiniaturizable
        )
        frame = NSMakeRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.window = DropWindow.alloc().initWithContentRect_styleMask_backing_defer_(frame, style, 2, False)
        self.window.setOwner_(self)
        self.window.setTitle_("Markdown 解析工具")
        self.window.setMinSize_((960, 640))
        self.window.setDelegate_(self)
        self.window.center()
        content_view = DropContentView.alloc().initWithFrame_owner_(self.window.contentView().frame(), self)
        self.window.setContentView_(content_view)
        content_view.setWantsLayer_(True)
        content_view.layer().setBackgroundColor_(rgb(244, 246, 251).CGColor())
        self.content_view = content_view

        split_height = WINDOW_HEIGHT
        self.split_view = DropSplitView.alloc().initWithFrame_owner_(NSMakeRect(0, 0, WINDOW_WIDTH, split_height), self)
        self.split_view.setVertical_(True)
        self.split_view.setDividerStyle_(1)
        self.split_view.setDelegate_(self)
        content_view.addSubview_(self.split_view)

        sidebar = self._build_sidebar(NSMakeRect(0, 0, SIDEBAR_WIDTH, split_height))
        viewer = self._build_viewer(NSMakeRect(SIDEBAR_WIDTH, 0, WINDOW_WIDTH - SIDEBAR_WIDTH, split_height))
        self.split_view.addSubview_(sidebar)
        self.split_view.addSubview_(viewer)
        self.split_view.setPosition_ofDividerAtIndex_(SIDEBAR_WIDTH, 0)
        self._layout_views()

    def _build_sidebar(self, frame):
        wrapper = DropContentView.alloc().initWithFrame_owner_(frame, self)
        wrapper.setWantsLayer_(True)
        wrapper.layer().setBackgroundColor_(rgb(255, 255, 255).CGColor())
        self.sidebar_wrapper = wrapper

        sidebar_padding = SIDEBAR_PADDING
        self.choose_button = NSButton.alloc().initWithFrame_(NSMakeRect(sidebar_padding, frame.size.height - 44, frame.size.width - sidebar_padding * 2, 30))
        self.choose_button.setTitle_("选择 .md 文件")
        self.choose_button.setBezelStyle_(NSBezelStyleRounded)
        self.choose_button.setTarget_(self)
        self.choose_button.setAction_("chooseFile:")
        self.choose_button.setHidden_(True)
        wrapper.addSubview_(self.choose_button)

        files_title = make_label(
            NSMakeRect(sidebar_padding, frame.size.height - 44, frame.size.width - sidebar_padding * 2, 24),
            "打开的文件",
            NSFont.boldSystemFontOfSize_(15),
            rgb(24, 33, 47),
        )
        self.files_title = files_title
        wrapper.addSubview_(files_title)

        list_left = SIDEBAR_LIST_LEFT_OFFSET
        list_width = frame.size.width - list_left - sidebar_padding
        self.file_scroll = DropScrollView.alloc().initWithFrame_owner_(NSMakeRect(list_left, sidebar_padding, list_width, frame.size.height - 70), self)
        self.file_scroll.setHasVerticalScroller_(True)

        self.file_table_view = DropTableView.alloc().initWithFrame_owner_(self.file_scroll.bounds(), self)
        column = NSTableColumn.alloc().initWithIdentifier_("files")
        delete_column = NSTableColumn.alloc().initWithIdentifier_("delete")
        delete_column.setWidth_(24)
        self.file_delete_column = delete_column
        column.setWidth_(max(120, list_width - 46))
        self.file_column = column
        file_cell = column.dataCell()
        file_cell.setEditable_(False)
        file_cell.setLineBreakMode_(NSLineBreakByTruncatingTail)
        file_cell.setWraps_(False)
        delete_cell = delete_column.dataCell()
        delete_cell.setEditable_(False)
        delete_cell.setLineBreakMode_(NSLineBreakByTruncatingTail)
        delete_cell.setWraps_(False)
        self.file_table_view.addTableColumn_(column)
        self.file_table_view.addTableColumn_(delete_column)
        self.file_table_view.setHeaderView_(None)
        self.file_table_view.setDataSource_(self)
        self.file_table_view.setDelegate_(self)
        self.file_table_view.setRowHeight_(28)
        self.file_table_view.setSelectionHighlightStyle_(NSTableViewSelectionHighlightStyleNone)
        self.file_table_view.setFocusRingType_(NSFocusRingTypeNone)
        self.file_table_view.setToolTip_("")
        self.file_scroll.setFocusRingType_(NSFocusRingTypeNone)
        self.file_scroll.setDocumentView_(self.file_table_view)
        wrapper.addSubview_(self.file_scroll)

        self.sidebar_drop_overlay = DropOverlayView.alloc().initWithFrame_owner_(
            NSMakeRect(list_left, sidebar_padding, list_width, frame.size.height - 70),
            self,
        )
        wrapper.addSubview_(self.sidebar_drop_overlay)
        return wrapper

    def _build_viewer(self, frame):
        wrapper = NSView.alloc().initWithFrame_(frame)
        wrapper.setWantsLayer_(True)
        wrapper.layer().setBackgroundColor_(rgb(244, 246, 251).CGColor())
        self.viewer_wrapper = wrapper

        self.path_label = make_label(
            NSMakeRect(PADDING, 8, frame.size.width - PADDING * 2, 20),
            "未选择文件",
            NSFont.systemFontOfSize_(12),
            rgb(92, 102, 117),
        )
        wrapper.addSubview_(self.path_label)

        config = WKWebViewConfiguration.alloc().init()
        config.setWebsiteDataStore_(WKWebsiteDataStore.nonPersistentDataStore())
        self.web_view = DropWebView.alloc().initWithFrame_configuration_owner_(
            NSMakeRect(0, PATH_BAR_HEIGHT, frame.size.width, frame.size.height - PATH_BAR_HEIGHT),
            config,
            self,
        )
        wrapper.addSubview_(self.web_view)
        self.viewer_drop_overlay = DropOverlayView.alloc().initWithFrame_owner_(
            NSMakeRect(0, PATH_BAR_HEIGHT, frame.size.width, frame.size.height - PATH_BAR_HEIGHT),
            self,
        )
        wrapper.addSubview_(self.viewer_drop_overlay)

        self.toc_dismiss_overlay = TocDismissOverlayView.alloc().initWithFrame_owner_(
            NSMakeRect(0, PATH_BAR_HEIGHT, frame.size.width, frame.size.height - PATH_BAR_HEIGHT),
            self,
        )
        self.toc_dismiss_overlay.setHidden_(True)
        wrapper.addSubview_(self.toc_dismiss_overlay)

        self.toc_button = NSButton.alloc().initWithFrame_(NSMakeRect(PADDING, frame.size.height - 48, TOC_BUTTON_SIZE, TOC_BUTTON_SIZE))
        self.toc_button.setTitle_("☰")
        self.toc_button.setToolTip_("文档目录")
        self.toc_button.setFont_(NSFont.boldSystemFontOfSize_(16))
        self.toc_button.setBordered_(False)
        self.toc_button.setTarget_(self)
        self.toc_button.setAction_("toggleTocPanel:")
        self.toc_button.setWantsLayer_(True)
        self.toc_button.layer().setCornerRadius_(10.0)
        self.toc_button.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.72).CGColor())
        wrapper.addSubview_(self.toc_button)

        self.toc_panel = NSView.alloc().initWithFrame_(NSMakeRect(PADDING, frame.size.height - 220, TOC_PANEL_WIDTH, 180))
        self.toc_panel.setHidden_(True)
        self.toc_panel.setWantsLayer_(True)
        self.toc_panel.layer().setCornerRadius_(14.0)
        self.toc_panel.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.88).CGColor())
        self.toc_panel.layer().setShadowColor_(NSColor.colorWithCalibratedWhite_alpha_(0.0, 1.0).CGColor())
        self.toc_panel.layer().setShadowOpacity_(0.18)
        self.toc_panel.layer().setShadowRadius_(16.0)
        self.toc_panel.layer().setShadowOffset_((0.0, -2.0))
        wrapper.addSubview_(self.toc_panel)

        self.toc_panel_title = make_label(
            NSMakeRect(14, 0, TOC_PANEL_WIDTH - 28, 24),
            "文档目录",
            NSFont.boldSystemFontOfSize_(14),
            rgb(36, 41, 47),
        )
        self.toc_panel.addSubview_(self.toc_panel_title)

        self.toc_scroll = DropScrollView.alloc().initWithFrame_owner_(NSMakeRect(12, 12, TOC_PANEL_WIDTH - 24, 132), self)
        self.toc_scroll.setHasVerticalScroller_(True)
        self.toc_scroll.setDrawsBackground_(False)
        self.toc_scroll.setFocusRingType_(NSFocusRingTypeNone)

        self.toc_table_view = DropTableView.alloc().initWithFrame_owner_(self.toc_scroll.bounds(), self)
        toc_column = NSTableColumn.alloc().initWithIdentifier_("toc")
        toc_column.setWidth_(TOC_PANEL_WIDTH - 42)
        self.toc_column = toc_column
        self.toc_table_view.addTableColumn_(toc_column)
        self.toc_table_view.setHeaderView_(None)
        self.toc_table_view.setDataSource_(self)
        self.toc_table_view.setDelegate_(self)
        self.toc_table_view.setRowHeight_(24)
        self.toc_table_view.setBackgroundColor_(NSColor.clearColor())
        self.toc_table_view.setFocusRingType_(NSFocusRingTypeNone)
        self.toc_scroll.setDocumentView_(self.toc_table_view)
        self.toc_panel.addSubview_(self.toc_scroll)
        return wrapper

    def _layout_views(self):
        content_bounds = self.content_view.bounds()
        width = content_bounds.size.width
        height = content_bounds.size.height

        split_height = height
        left_width = self.split_view.subviews()[0].frame().size.width if self.split_view.subviews() else SIDEBAR_WIDTH
        if left_width < 220:
            left_width = 220
        if left_width > max(220, width - 320):
            left_width = max(220, width - 320)

        self.split_view.setFrame_(NSMakeRect(0, 0, width, split_height))
        self.split_view.setPosition_ofDividerAtIndex_(left_width, 0)
        self._layout_split_content()

    def _layout_split_content(self):
        sidebar_bounds = self.sidebar_wrapper.bounds()
        sidebar_width = sidebar_bounds.size.width
        sidebar_height = sidebar_bounds.size.height
        sidebar_padding = SIDEBAR_PADDING
        list_left = SIDEBAR_LIST_LEFT_OFFSET
        list_width = sidebar_width - list_left - sidebar_padding
        self.choose_button.setFrame_(NSMakeRect(sidebar_padding, sidebar_height - 44, sidebar_width - sidebar_padding * 2, 30))
        self.files_title.setFrame_(NSMakeRect(sidebar_padding, sidebar_height - 44, sidebar_width - sidebar_padding * 2, 24))
        self.file_scroll.setFrame_(NSMakeRect(list_left, sidebar_padding, list_width, sidebar_height - 70))
        self.file_table_view.setFrame_(self.file_scroll.bounds())
        self.sidebar_drop_overlay.setFrame_(NSMakeRect(list_left, sidebar_padding, list_width, sidebar_height - 70))
        self.file_delete_column.setWidth_(24)
        self.file_column.setWidth_(max(120, list_width - 46))

        viewer_bounds = self.viewer_wrapper.bounds()
        viewer_width = viewer_bounds.size.width
        viewer_height = viewer_bounds.size.height
        self.path_label.setFrame_(NSMakeRect(PADDING, 8, viewer_width - PADDING * 2, 20))
        self.web_view.setFrame_(NSMakeRect(0, PATH_BAR_HEIGHT, viewer_width, viewer_height - PATH_BAR_HEIGHT))
        self.viewer_drop_overlay.setFrame_(NSMakeRect(0, PATH_BAR_HEIGHT, viewer_width, viewer_height - PATH_BAR_HEIGHT))
        self.toc_dismiss_overlay.setFrame_(NSMakeRect(0, PATH_BAR_HEIGHT, viewer_width, viewer_height - PATH_BAR_HEIGHT))
        self.toc_button.setFrame_(NSMakeRect(PADDING, viewer_height - 52, TOC_BUTTON_SIZE, TOC_BUTTON_SIZE))
        panel_width = min(TOC_PANEL_WIDTH, max(220, viewer_width - PADDING * 2))
        panel_height = min(TOC_PANEL_MAX_HEIGHT, max(150, viewer_height - 110))
        panel_y = max(PATH_BAR_HEIGHT + 12, viewer_height - 64 - panel_height)
        self.toc_panel.setFrame_(NSMakeRect(PADDING, panel_y, panel_width, panel_height))
        self.toc_panel_title.setFrame_(NSMakeRect(14, panel_height - 34, panel_width - 28, 22))
        self.toc_scroll.setFrame_(NSMakeRect(12, 12, panel_width - 24, panel_height - 52))
        self.toc_table_view.setFrame_(self.toc_scroll.bounds())
        self.toc_column.setWidth_(max(120, panel_width - 42))

    def open_file_on_startup(self):
        if len(sys.argv) > 1:
            self.load_files(sys.argv[1:])

    def _extract_markdown_paths(self, pasteboard):
        file_paths = pasteboard.propertyListForType_(NSFilenamesPboardType) or []
        if not file_paths:
            file_url = pasteboard.stringForType_(NSPasteboardTypeFileURL)
            if file_url:
                url = NSURL.URLWithString_(file_url)
                if url:
                    path = url.path()
                    file_paths = [path] if path else []

        markdown_paths = []
        seen_paths = set()
        for file_path in file_paths:
            markdown_path = self._normalize_markdown_path(file_path)
            if markdown_path and markdown_path not in seen_paths:
                seen_paths.add(markdown_path)
                markdown_paths.append(markdown_path)
        return markdown_paths

    def _extract_markdown_path(self, pasteboard):
        markdown_paths = self._extract_markdown_paths(pasteboard)
        if markdown_paths:
            return markdown_paths[0]
        return None

    def _load_pasteboard_files(self, pasteboard):
        return self.load_files(self._extract_markdown_paths(pasteboard))

    def _normalize_markdown_path(self, file_path):
        if not file_path or not os.path.isfile(file_path):
            return None
        extension = os.path.splitext(file_path)[1].lower()
        if extension in [".md", ".markdown"]:
            return file_path
        return None

    def show_placeholder(self):
        html = """<!DOCTYPE html><html><body style="margin:0;height:100vh;overflow:hidden;background:#f6f8fa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
        <div style="height:100%;padding:24px;">
          <div style="height:100%;background:#fff;border:1px solid #d0d7de;border-radius:12px;box-shadow:0 8px 28px rgba(31,35,40,.08);overflow:auto;">
            <div style="max-width:760px;margin:80px auto;padding:40px;">
              <h1 style="margin:0 0 12px;color:#24292f;">请选择 Markdown 文件</h1>
              <p style="margin:0;color:#57606a;">左侧点击“选择 .md 文件”或直接拖入窗口打开；已打开文件会保留在左侧列表，右上角文档目录默认展开，点击空白区域可收起。</p>
            </div>
          </div>
        </div></body></html>"""
        self.web_view.loadHTMLString_baseURL_(html, NSURL.fileURLWithPath_(resource_path("")))

    def load_file(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="utf-8-sig") as handle:
                content = handle.read()

        self.current_file = file_path
        title, html, toc_items, block_count = render_markdown_html(content, os.path.basename(file_path))
        self.heading_targets = toc_items
        self._remember_opened_file(file_path)

        self.path_label.setStringValue_(file_path)
        self.file_table_view.reloadData()
        self.toc_table_view.reloadData()
        self._select_current_file_in_list()
        self.web_view.loadHTMLString_baseURL_(html, NSURL.fileURLWithPath_(resource_path("")))

    def load_files(self, file_paths):
        normalized_paths = []
        seen_paths = set()
        for file_path in file_paths:
            markdown_path = self._normalize_markdown_path(file_path)
            if markdown_path and markdown_path not in seen_paths:
                seen_paths.add(markdown_path)
                normalized_paths.append(markdown_path)
        if not normalized_paths:
            return False
        for file_path in normalized_paths:
            self._remember_opened_file(file_path)
        self.load_file(normalized_paths[0])
        return True

    def _remember_opened_file(self, file_path):
        if file_path not in self.opened_files:
            self.opened_files.append(file_path)

    def _select_current_file_in_list(self):
        if not self.current_file:
            return
        try:
            row = self.opened_files.index(self.current_file)
        except ValueError:
            return
        self.file_table_view.selectRowIndexes_byExtendingSelection_(NSIndexSet.indexSetWithIndex_(row), False)

    def remove_opened_file_at_row(self, row):
        if row < 0 or row >= len(self.opened_files):
            return
        removed_path = self.opened_files.pop(row)
        if not self.opened_files:
            self.clear_opened_files()
            return
        if removed_path == self.current_file:
            next_row = min(row, len(self.opened_files) - 1)
            self.load_file(self.opened_files[next_row])
            return
        self.file_table_view.reloadData()
        self._select_current_file_in_list()

    def clear_opened_files(self):
        self.opened_files = []
        self.current_file = None
        self.heading_targets = []
        self.path_label.setStringValue_("未选择文件")
        self.file_table_view.reloadData()
        self.toc_table_view.reloadData()
        self._set_toc_panel_visible(False)
        self.show_placeholder()

    def _set_toc_panel_visible(self, visible):
        self.toc_panel_visible = visible
        self.toc_panel.setHidden_(not visible)
        self.toc_dismiss_overlay.setHidden_(not visible)
        alpha = 0.92 if visible else 0.72
        self.toc_button.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, alpha).CGColor())


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    delegate = MarkdownAppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()



d650be79 (origin/fix_bug_260929, fix_bug_260929) chagne file
63c751bc 腾讯验证码
007d52f4 腾讯滑块验证