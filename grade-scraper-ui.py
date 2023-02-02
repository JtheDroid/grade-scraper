from concurrent.futures.thread import ThreadPoolExecutor

import wx
from wx.adv import TaskBarIcon as TaskBarIcon
from main import main, load_settings, save_settings

timer_period = 1000 * 60  # 1 min


class MyTaskBarIcon(TaskBarIcon):
    def __init__(self, frame):
        TaskBarIcon.__init__(self)

        self.frame = frame
        self.SetIcon(wx.Icon('./scuffed-icon.png', wx.BITMAP_TYPE_PNG), 'grade-scraper')

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

        close_btn = wx.Button(pnl, label="Close")
        self.Bind(wx.EVT_BUTTON, self.exit, close_btn)
        sizer.AddStretchSpacer()
        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        start_btn = wx.Button(pnl, label="Start")
        self.Bind(wx.EVT_BUTTON, self.start, start_btn)
        btn_row.Add(start_btn, wx.SizerFlags().Border(wx.ALL, 5))
        btn_row.AddStretchSpacer()
        stop_btn = wx.Button(pnl, label="Stop")
        self.Bind(wx.EVT_BUTTON, self.stop, stop_btn)
        btn_row.Add(stop_btn, wx.SizerFlags().Border(wx.ALL, 5))
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

    def stop(self, _event=None):
        self.timer.Stop()

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


class MyApp(wx.App):
    def OnInit(self):
        frame = GradeScraperUI(None, -1, icon=wx.Icon("./scuffed-icon.png", wx.BITMAP_TYPE_PNG))
        frame.Show(True)
        self.SetTopWindow(frame)

        return True


if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
