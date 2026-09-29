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
    NSOpenPanel,
    NSPasteboardTypeFileURL,
    NSRunningApplication,
    NSScrollView,
    NSSplitView,
    NSTableColumn,
    NSTableView,
    NSTextField,
    NSFilenamesPboardType,
    NSFocusRingTypeNone,
    NSView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSObject, NSURL
from WebKit import WKWebView, WKWebViewConfiguration, WKWebsiteDataStore

from html_renderer import render_markdown_html


WINDOW_WIDTH = 1220
WINDOW_HEIGHT = 780
SIDEBAR_WIDTH = 290
PADDING = 18
PATH_BAR_HEIGHT = 34


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
        file_path = self.owner._extract_markdown_path(sender.draggingPasteboard())
        if not file_path:
            return False
        self.owner.load_file(file_path)
        return True


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
        file_path = self.owner._extract_markdown_path(sender.draggingPasteboard())
        if not file_path:
            return False
        self.owner.load_file(file_path)
        return True


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
        file_path = self.owner._extract_markdown_path(sender.draggingPasteboard())
        if not file_path:
            return False
        self.owner.load_file(file_path)
        return True


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
        file_path = self.owner._extract_markdown_path(sender.draggingPasteboard())
        if not file_path:
            return False
        self.owner.load_file(file_path)
        return True


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
        file_path = self.owner._extract_markdown_path(sender.draggingPasteboard())
        if not file_path:
            return False
        self.owner.load_file(file_path)
        return True


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
        file_path = self.owner._extract_markdown_path(sender.draggingPasteboard())
        if not file_path:
            return False
        self.owner.load_file(file_path)
        return True


class MarkdownAppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, _notification):
        self.current_file = None
        self.heading_targets = []
        self._build_window()
        self.window.makeKeyAndOrderFront_(None)
        NSRunningApplication.currentApplication().activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        self.show_placeholder()
        self.open_file_on_startup()

    def applicationShouldTerminateAfterLastWindowClosed_(self, _app):
        return True

    def numberOfRowsInTableView_(self, _table_view):
        return len(self.heading_targets)

    def tableView_objectValueForTableColumn_row_(self, _table_view, _column, row):
        if row >= len(self.heading_targets):
            return ""
        level, title, _anchor = self.heading_targets[row]
        return "%s%s" % ("  " * max(level - 1, 0), title)

    def tableViewSelectionDidChange_(self, notification):
        row = notification.object().selectedRow()
        if 0 <= row < len(self.heading_targets):
            _level, _title, anchor = self.heading_targets[row]
            script = "scrollToHeading(%s);" % json.dumps(anchor)
            self.web_view.evaluateJavaScript_completionHandler_(script, None)

    def chooseFile_(self, _sender):
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(False)
        panel.setAllowsMultipleSelection_(False)
        panel.setAllowedFileTypes_(["md", "markdown"])
        panel.setTitle_("选择 Markdown 文件")
        if panel.runModal() == 1:
            url = panel.URL()
            if url:
                self.load_file(url.path())

    def windowDidResize_(self, _notification):
        self._layout_views()

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
        content_view.addSubview_(self.split_view)

        sidebar = self._build_sidebar(NSMakeRect(0, 0, SIDEBAR_WIDTH, split_height))
        viewer = self._build_viewer(NSMakeRect(SIDEBAR_WIDTH, 0, WINDOW_WIDTH - SIDEBAR_WIDTH, split_height))
        self.split_view.addSubview_(sidebar)
        self.split_view.addSubview_(viewer)
        self.split_view.setPosition_ofDividerAtIndex_(SIDEBAR_WIDTH, 0)
        self._layout_views()

    def _build_sidebar(self, frame):
        wrapper = NSView.alloc().initWithFrame_(frame)
        wrapper.setWantsLayer_(True)
        wrapper.layer().setBackgroundColor_(rgb(255, 255, 255).CGColor())
        self.sidebar_wrapper = wrapper

        self.choose_button = NSButton.alloc().initWithFrame_(NSMakeRect(PADDING, frame.size.height - 46, frame.size.width - PADDING * 2, 32))
        self.choose_button.setTitle_("选择 .md 文件")
        self.choose_button.setBezelStyle_(NSBezelStyleRounded)
        self.choose_button.setTarget_(self)
        self.choose_button.setAction_("chooseFile:")
        wrapper.addSubview_(self.choose_button)

        toc_title = make_label(
            NSMakeRect(PADDING, frame.size.height - 84, frame.size.width - PADDING * 2, 28),
            "文档目录",
            NSFont.boldSystemFontOfSize_(16),
            rgb(24, 33, 47),
        )
        self.toc_title = toc_title
        wrapper.addSubview_(toc_title)

        self.toc_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(PADDING, PADDING, frame.size.width - PADDING * 2, frame.size.height - 126))
        self.toc_scroll.setHasVerticalScroller_(True)

        self.table_view = DropTableView.alloc().initWithFrame_owner_(self.toc_scroll.bounds(), self)
        column = NSTableColumn.alloc().initWithIdentifier_("toc")
        column.setWidth_(frame.size.width - PADDING * 2 - 18)
        self.toc_column = column
        self.table_view.addTableColumn_(column)
        self.table_view.setHeaderView_(None)
        self.table_view.setDataSource_(self)
        self.table_view.setDelegate_(self)
        self.table_view.setRowHeight_(24)
        self.table_view.setFocusRingType_(NSFocusRingTypeNone)
        self.toc_scroll.setFocusRingType_(NSFocusRingTypeNone)
        self.toc_scroll.setDocumentView_(self.table_view)
        wrapper.addSubview_(self.toc_scroll)
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

        sidebar_bounds = self.sidebar_wrapper.bounds()
        sidebar_width = sidebar_bounds.size.width
        sidebar_height = sidebar_bounds.size.height
        self.choose_button.setFrame_(NSMakeRect(PADDING, sidebar_height - 46, sidebar_width - PADDING * 2, 32))
        self.toc_title.setFrame_(NSMakeRect(PADDING, sidebar_height - 84, sidebar_width - PADDING * 2, 28))
        self.toc_scroll.setFrame_(NSMakeRect(PADDING, PADDING, sidebar_width - PADDING * 2, sidebar_height - 126))
        self.toc_column.setWidth_(max(120, sidebar_width - PADDING * 2 - 18))

        viewer_bounds = self.viewer_wrapper.bounds()
        viewer_width = viewer_bounds.size.width
        viewer_height = viewer_bounds.size.height
        self.path_label.setFrame_(NSMakeRect(PADDING, 8, viewer_width - PADDING * 2, 20))
        self.web_view.setFrame_(NSMakeRect(0, PATH_BAR_HEIGHT, viewer_width, viewer_height - PATH_BAR_HEIGHT))
        self.viewer_drop_overlay.setFrame_(NSMakeRect(0, PATH_BAR_HEIGHT, viewer_width, viewer_height - PATH_BAR_HEIGHT))

    def open_file_on_startup(self):
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            self.load_file(sys.argv[1])
            return
        self.chooseFile_(None)

    def _extract_markdown_path(self, pasteboard):
        file_paths = pasteboard.propertyListForType_(NSFilenamesPboardType) or []
        if not file_paths:
            file_url = pasteboard.stringForType_(NSPasteboardTypeFileURL)
            if file_url:
                url = NSURL.URLWithString_(file_url)
                if url:
                    path = url.path()
                    file_paths = [path] if path else []

        for file_path in file_paths:
            if not file_path or not os.path.isfile(file_path):
                continue
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
              <p style="margin:0;color:#57606a;">左侧点击“选择 .md 文件”，或直接把 Markdown 文件拖入窗口，即可用 GitHub 风格查看文档，并预览 Mermaid 流程图。</p>
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

        self.path_label.setStringValue_(file_path)
        self.table_view.reloadData()
        self.web_view.loadHTMLString_baseURL_(html, NSURL.fileURLWithPath_(resource_path("")))


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    delegate = MarkdownAppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
