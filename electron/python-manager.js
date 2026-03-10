const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const { app } = require('electron');

class PythonManager {
  constructor() {
    this.process = null;
  }

  async start() {
    const isDev = !app.isPackaged;

    // In dev mode, backend is already managed by concurrently (npm run dev)
    if (isDev) {
      return;
    }

    const command = path.join(process.resourcesPath, 'backend', 'code-agent-backend');
    const args = ['--port', '8000'];
    const cwd = path.join(process.resourcesPath, 'backend');

    this.process = spawn(command, args, {
      cwd,
      env: { ...process.env },
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    this.process.stdout.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
    });

    this.process.stderr.on('data', (data) => {
      console.error(`[Backend] ${data.toString().trim()}`);
    });

    this.process.on('exit', (code) => {
      console.log(`[Backend] Process exited with code ${code}`);
    });

    await this._waitForReady(30000);
  }

  async stop() {
    if (this.process) {
      this.process.kill('SIGTERM');
      // Give it 5 seconds to gracefully shutdown
      await new Promise((resolve) => {
        const timeout = setTimeout(() => {
          if (this.process) this.process.kill('SIGKILL');
          resolve();
        }, 5000);

        this.process.on('exit', () => {
          clearTimeout(timeout);
          resolve();
        });
      });
      this.process = null;
    }
  }

  _waitForReady(timeoutMs) {
    return new Promise((resolve, reject) => {
      const start = Date.now();

      const check = () => {
        if (Date.now() - start > timeoutMs) {
          return reject(new Error('Backend did not start within timeout'));
        }

        const req = http.get('http://localhost:8000/health', (res) => {
          if (res.statusCode === 200) {
            resolve();
          } else {
            setTimeout(check, 500);
          }
        });

        req.on('error', () => {
          setTimeout(check, 500);
        });

        req.end();
      };

      setTimeout(check, 1000); // Initial delay
    });
  }
}

module.exports = { PythonManager };
