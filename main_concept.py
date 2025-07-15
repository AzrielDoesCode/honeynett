

# main.py
import subprocess, sys, os, time, shutil, threading, queue, signal
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer, Log
from textual.reactive import reactive

# --------- CONFIG ----------------------------------------------------------
HONEYPOTS = {
    "SSH"   : ("ssh_honeypot.py",   2223, "audits.log"),
    "TCP"   : ("tcp_honeypot.py",   8080, "tcp_audits.log"),
    "HTTPS" : ("https_honeypot.py", 8443, "https_audits.log"),
    "FTP"   : ("ftp_honeypot.py",   2121, "ftp_audits.log"),
    "MySQL" : ("mysql_honeypot.py", 3307, "mysql_audits.log"),
}

PYTHON_EXEC = shutil.which("python3") or sys.executable
LOG_TAIL_LINES = 3
# --------------------------------------------------------------------------

class PotStatus(Static):
    running: reactive[bool] = reactive(False)

    def render(self):
        name = self.id.upper()
        status = "RUNNING" if self.running else "DOWN   "
        color  = "green" if self.running else "red"
        return f"[bold]{name:<6}[/] • [{color}]{status}[/]"

class HoneyNetApp(App):
    CSS = "Screen {align: center middle}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.procs = {}          # name -> subprocess
        self.log_q = queue.Queue()
        self.active = "SSH"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        for name in HONEYPOTS:
            yield PotStatus(id=name)
        yield Log(id="logbox")
        yield Footer()

    def _spawn_pot(self, name, script, port):
        return subprocess.Popen(
            [PYTHON_EXEC, script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "HONEYPOT_PORT": str(port)},
        )

    def on_mount(self):
        Path("logs").mkdir(exist_ok=True)
        for name, (script, port, _) in HONEYPOTS.items():
            self.procs[name] = self._spawn_pot(name, script, port)
        threading.Thread(target=self._watcher, daemon=True).start()
        self.set_interval(1, self._refresh_status)
        self._update_logbox()

    def _watcher(self):
        import tailer
        file_handles = {
            name: open(log, "r", errors="ignore")
            for name, (_, _, log) in HONEYPOTS.items()
        }
        for fh in file_handles.values():
            fh.seek(0, os.SEEK_END)
        while True:
            for name, fh in file_handles.items():
                for line in tailer.follow(fh, delay=0.1):
                    self.log_q.put((name, line.rstrip()))
            time.sleep(0.1)

    def _refresh_status(self):
        for name, proc in self.procs.items():
            self.query_one(f"#{name}", PotStatus).running = proc.poll() is None
        processed = False
        while not self.log_q.empty():
            name, line = self.log_q.get()
            if name == self.active:
                self.query_one("#logbox", Log).write(line)
                processed = True
        if processed:
            logbox = self.query_one("#logbox", Log)
            logbox.clear()
            latest = Path(HONEYPOTS[self.active][2]).read_text().splitlines()[-LOG_TAIL_LINES:]
            for l in latest:
                logbox.write(l)

    def key_1(self): self._switch_active("SSH")
    def key_2(self): self._switch_active("TCP")
    def key_3(self): self._switch_active("HTTPS")
    def key_4(self): self._switch_active("FTP")
    def key_5(self): self._switch_active("MySQL")

    def _switch_active(self, name):
        self.active = name
        self._update_logbox()


    def _update_logbox(self):
        logbox = self.query_one("#logbox", Log)
        logbox.clear()
        log_file = Path(HONEYPOTS[self.active][2])
        if log_file.exists():
            for line in log_file.read_text().splitlines()[-LOG_TAIL_LINES:]:
                logbox.write(line)

    def on_exit(self):
        for proc in self.procs.values():
            proc.terminate()

if __name__ == "__main__":
    HoneyNetApp().run()
