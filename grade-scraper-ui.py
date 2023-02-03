from concurrent.futures.thread import ThreadPoolExecutor

import sys
import os
import wx
from wx.adv import TaskBarIcon as TaskBarIcon
from main import (
    main, load_settings, save_settings, default_settings, create_settings,
    webdriver_setting_mapping, setting_webdriver_type, setting_users, setting_username, setting_password
)

timer_period = 1000 * 60  # 1 min


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MyTaskBarIcon(TaskBarIcon):
    def __init__(self, frame):
        TaskBarIcon.__init__(self)

        self.frame = frame
        self.SetIcon(wx.Icon(resource_path('scuffed-icon.png'), wx.BITMAP_TYPE_PNG), 'grade-scraper')

        # ------------
        self.Bind(wx.EVT_MENU, self.OnTaskBarActivate, id=1)
        self.Bind(wx.EVT_MENU, self.OnTaskBarDeactivate, id=2)
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=3)

    # -----------------------------------------------------------------------

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(1, 'Show')
        menu.Append(2, 'Hide')
        menu.Append(3, 'Close')

        return menu

    def OnTaskBarClose(self, event):
        self.frame.Close()

    def OnTaskBarActivate(self, event):
        if not self.frame.IsShown():
            self.frame.Show()

    def OnTaskBarDeactivate(self, event):
        if self.frame.IsShown():
            self.frame.Hide()


class GradeScraperUI(wx.Frame):
    def __init__(self, *args, icon=None, **kw):
        super(GradeScraperUI, self).__init__(*args, title="grade-scraper", **kw)

        if icon:
            self.SetIcon(icon)

        pnl = wx.Panel(self)
        self.panel = pnl
        self.taskicon = MyTaskBarIcon(self)
        self.threadpool = ThreadPoolExecutor()
        self.future = None
        self.scrape_period_minutes = 15
        self.minutes_left = self.scrape_period_minutes

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.status_text = wx.StaticText(pnl, label="Click 'Start' to start")
        sizer.Add(self.status_text, wx.SizerFlags().Border(wx.ALL, 5))

        settings = None
        try:
            settings = load_settings()
        except FileNotFoundError:
            settings = default_settings()
            create_settings()

        settings_sizer = wx.StaticBoxSizer(wx.VERTICAL, pnl, "Einstellungen")
        settings_grid = wx.FlexGridSizer(cols=2, gap=wx.Size(5, 5))
        settings_grid.AddGrowableCol(1, 1)
        settings_grid.SetFlexibleDirection(wx.VERTICAL)

        def add_text_setting(label, **kwargs) -> wx.TextCtrl:
            settings_grid.Add(wx.StaticText(pnl, label=label))
            txt_ctrl = wx.TextCtrl(pnl, **kwargs)
            settings_grid.Add(txt_ctrl, wx.SizerFlags(1).Expand())
            return txt_ctrl

        self.text_username = add_text_setting(
            "HAWK Nutzername", value=settings[setting_users][0][setting_username]
        )
        self.text_password = add_text_setting(
            "HAWK Passwort", style=wx.TE_PASSWORD, value=settings[setting_users][0][setting_password]
        )

        rbtns = wx.BoxSizer(wx.VERTICAL)
        settings_grid.Add(wx.StaticText(pnl, label="Browser"))
        settings_grid.Add(rbtns)

        self.webdriver_rbs: dict[str, wx.RadioButton] = {}
        for name, key in webdriver_setting_mapping.items():
            rb = wx.RadioButton(pnl, label=name)
            rbtns.Add(rb)
            self.webdriver_rbs[key] = rb
        del rb

        for key, rb in self.webdriver_rbs.items():
            if settings[setting_webdriver_type] == key:
                rb.SetValue(True)
                break

        save_btn = wx.Button(pnl, label="Save")
        settings_grid.Add(save_btn)
        self.Bind(wx.EVT_BUTTON, self.save_settings, save_btn)

        settings_sizer.Add(settings_grid, wx.SizerFlags().Expand())
        sizer.Add(settings_sizer, wx.SizerFlags().Expand().Border(wx.ALL, 5))

        close_btn = wx.Button(pnl, label="Close")
        self.Bind(wx.EVT_BUTTON, self.exit, close_btn)
        sizer.AddStretchSpacer()
        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(pnl, label="Start")
        self.Bind(wx.EVT_BUTTON, self.start, self.start_btn)
        btn_row.Add(self.start_btn, wx.SizerFlags().Border(wx.ALL, 5))
        btn_row.AddStretchSpacer()
        self.stop_btn = wx.Button(pnl, label="Stop")
        self.stop_btn.Disable()
        self.Bind(wx.EVT_BUTTON, self.stop, self.stop_btn)
        btn_row.Add(self.stop_btn, wx.SizerFlags().Border(wx.ALL, 5))
        sizer.Add(btn_row, wx.SizerFlags(1).Expand())
        sizer.Add(close_btn, wx.SizerFlags().Border(wx.ALL, 5).Right())

        pnl.SetSizer(sizer)
        min_size: wx.Size = sizer.GetMinSize()
        min_size.IncBy(dx=0, dy=0)
        self.SetMinClientSize(min_size)
        self.Fit()

        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER, self._timer_fired)

        self.Bind(wx.EVT_CLOSE, self.exit, self)

    def exit(self, _event):
        self.threadpool.shutdown()
        self.threadpool = None
        self.taskicon.Destroy()
        self.Destroy()

    def start(self, _event=None):
        self.scrape()
        self.minutes_left = self.scrape_period_minutes
        self.timer.Start(timer_period)
        self.stop_btn.Enable()
        self.start_btn.Disable()

    def stop(self, _event=None):
        self.timer.Stop()
        self.stop_btn.Disable()
        self.start_btn.Enable()

    def scrape(self):
        self.future = self.threadpool.submit(main)
        self.future.add_done_callback(self.done_scraping_callback)
        self.status_text.SetLabel("Getting grades")

    def done_scraping_callback(self, future):
        self.future = None
        self.status_text.SetLabel("Done getting grades")

    def _timer_fired(self, _event=None):
        self.minutes_left -= 1
        if self.minutes_left == 0:
            self.scrape()
            self.minutes_left = self.scrape_period_minutes
        elif self.future is None:
            self.status_text.SetLabel(f"{self.minutes_left} minutes until getting grades")

    def save_settings(self, _event=None):
        settings = load_settings()
        for key, rb in self.webdriver_rbs.items():
            if rb.GetValue():
                settings[setting_webdriver_type] = key
                break
        settings[setting_users][0][setting_username] = self.text_username.GetValue()
        settings[setting_users][0][setting_password] = self.text_password.GetValue()
        save_settings(settings)


class MyApp(wx.App):
    def OnInit(self):
        frame = GradeScraperUI(None, -1, icon=wx.Icon(resource_path('scuffed-icon.png'), wx.BITMAP_TYPE_PNG))
        frame.Show(True)
        self.SetTopWindow(frame)

        return True


if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
