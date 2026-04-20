from flask import Flask, render_template

app = Flask(__name__)

# Global variable to track the scan count
scan_count = 0

@app.route('/')
def index():
    global scan_count
    return render_template('index.html', scan_count=scan_count)

@app.route('/scan')
def scan():
    global scan_count
    scan_count += 1
    return "QR Code scanned successfully!"

if __name__ == '__main__':
    app.run(debug=True)
