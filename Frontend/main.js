const { app, BrowserWindow, screen } = require("electron");
const path = require("path");

function createWindow() {
    const { width, height } = screen.getPrimaryDisplay().workAreaSize;

    const win = new BrowserWindow({
        width: width,
        height: height,
        x: 0,
        y: 0,
        transparent: true,
        frame: false,
        alwaysOnTop: true,
        hasShadow: false,
        resizable: false,
        skipTaskbar: true,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        },
    });

    // Make window click-through
    win.setIgnoreMouseEvents(true, { forward: true });

    // Ensure it stays on top of fullscreen apps
    win.setAlwaysOnTop(true, "screen-saver");
    win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

    win.loadFile("index.html");
}

app.whenReady().then(() => {
    setTimeout(createWindow, 1000); // Slight delay to ensure display readiness
});

app.on("window-all-closed", () => {
    if (process.platform !== "darwin") app.quit();
});