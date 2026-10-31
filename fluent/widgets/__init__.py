"""Fluent 控件集合。

所有控件依赖 PySide6（Qt for Python，LGPL 协议，可免费商用）。
"""
from .button import FluentButton
from .calendar import FluentCalendarView, FluentDateRangePicker
from .card import FluentCard, FluentSettingsCard
from .charts import (FluentAreaChart, FluentBarChart, FluentGaugeChart,
                     FluentLineChart, FluentPieChart, SERIES_COLORS)
from .charts2 import (FluentFunnelChart, FluentGanttChart, FluentHeatmapChart,
                      FluentRadarChart, FluentScatterChart)
from .charts3 import FluentBoxChart, FluentTimeSeriesChart
from .checkbox import (FluentCheckBox, FluentRadioButton, make_radio_group)
from .colorpicker import (FluentColorButton, FluentColorDialog,
                          FluentColorPicker, PRESET_COLORS)
from .combobox import FluentComboBox
from .commandbar import FluentCommandBar, FluentSplitButton
from .datetime import FluentDatePicker, FluentTimePicker
from .dialogs import FluentInputDialog, FluentProgressDialog
from .effects import (FluentAcrylicCard, FluentAnimatedWidget,
                      FluentRevealButton)
from .expander import FluentExpander, FluentGroupBox
from .form import FluentForm
from .i18n import FluentTranslator
from .icons import CloseButton, IconBadge
from .imageviewer import FluentAudioVisualizer, FluentImageViewer
from .infobar import FluentInfoBar
from .layout import (FluentBreadcrumbBar, FluentFlowLayout, FluentNavigationView,
                     FluentSplitter)
from .lineedit import FluentLineEdit, FluentTextEdit
from .linkbutton import FluentHyperlinkButton, FluentTag
from .listview import FluentListItem, FluentListView
from .messagebox import FluentMessageBox
from .misc import FluentAvatar, FluentQuantitySelector, FluentRating
from .navigation import FluentNavigation
from .pagedtable import FluentPagedTable
from .progressbar import FluentProgressBar
from .progressring import FluentProgressRing
from .searchbox import FluentSearchBox
from .slider import FluentSlider
from .spinbox import FluentDoubleSpinBox, FluentSpinBox
from .table import FluentTableWidget, FluentTreeView
from .tabs import FluentTabWidget
from .text import FluentMarkdownViewer, FluentRichTextEditor, markdown_to_html
from .tile import FluentGridView, FluentTile
from .titlebar import (FluentFramelessWindow, FluentTitleBar, enable_acrylic,
                       enable_blur_behind)
from .toast import FluentTeachingTip, FluentToast, FluentTooltip
from .toggle import FluentToggleSwitch
from .tray import (FluentNotificationCenter, FluentSystemDialog, FluentTrayIcon,
                   make_letter_icon)
from .treetable import FluentTreeTable

__all__ = [
    "FluentButton",
    "FluentCard",
    "FluentSettingsCard",
    "FluentCalendarView",
    "FluentDateRangePicker",
    "FluentLineChart",
    "FluentAreaChart",
    "FluentBarChart",
    "FluentPieChart",
    "FluentGaugeChart",
    "FluentScatterChart",
    "FluentHeatmapChart",
    "FluentRadarChart",
    "FluentFunnelChart",
    "FluentGanttChart",
    "FluentBoxChart",
    "FluentTimeSeriesChart",
    "SERIES_COLORS",
    "FluentInputDialog",
    "FluentProgressDialog",
    "FluentImageViewer",
    "FluentAudioVisualizer",
    "FluentTreeTable",
    "FluentAcrylicCard",
    "FluentRevealButton",
    "FluentAnimatedWidget",
    "FluentTrayIcon",
    "FluentSystemDialog",
    "FluentNotificationCenter",
    "make_letter_icon",
    "FluentForm",
    "FluentTranslator",
    "FluentFramelessWindow",
    "FluentTitleBar",
    "enable_acrylic",
    "enable_blur_behind",
    "FluentPagedTable",
    "FluentSplitter",
    "FluentFlowLayout",
    "FluentBreadcrumbBar",
    "FluentNavigationView",
    "FluentMarkdownViewer",
    "FluentRichTextEditor",
    "markdown_to_html",
    "FluentCheckBox",
    "FluentRadioButton",
    "make_radio_group",
    "FluentComboBox",
    "FluentCommandBar",
    "FluentSplitButton",
    "FluentDatePicker",
    "FluentTimePicker",
    "FluentExpander",
    "FluentGroupBox",
    "FluentAvatar",
    "FluentRating",
    "FluentQuantitySelector",
    "FluentTableWidget",
    "FluentTreeView",
    "FluentTile",
    "FluentGridView",
    "FluentToast",
    "FluentTooltip",
    "FluentTeachingTip",
    "FluentColorButton",
    "FluentColorDialog",
    "FluentColorPicker",
    "PRESET_COLORS",
    "FluentLineEdit",
    "FluentTextEdit",
    "FluentInfoBar",
    "FluentMessageBox",
    "FluentSpinBox",
    "FluentDoubleSpinBox",
    "FluentSearchBox",
    "FluentTabWidget",
    "FluentProgressBar",
    "FluentProgressRing",
    "FluentListView",
    "FluentListItem",
    "FluentNavigation",
    "FluentHyperlinkButton",
    "FluentTag",
    "CloseButton",
    "IconBadge",
]
