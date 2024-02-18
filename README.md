### SecureFace: AES Encrypted Facial Authentication Application

SecureFace is a facial authentication application designed to provide secure authentication using AES encryption and two-factor authentication (2FA). Follow the steps below to install the necessary dependencies and execute the program.



#### Installation:

1. Clone the repository:

```bash
git clone https://github.com/riccardolops/SecureFace
cd SecureFace
```

2. Set up a virtual environment (recommended):

```bash
python3 -m venv venv
```

3. Activate the virtual environment:

   - On Windows:

   ```bash
   venv\Scripts\activate
   ```

   - On macOS and Linux:

   ```bash
   source venv/bin/activate
   ```

4. Install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

#### Execution:

Once the dependencies are installed, you can execute the program by running the `main.py` file:

```bash
python main.py
```

Follow the on-screen instructions to utilize the SecureFace application for facial authentication. If you encounter any issues or have any questions, please refer to the documentation or contact the maintainers.

#### Notes:

- It's recommended to use a virtual environment to isolate the project dependencies.
- Ensure that your environment has access to a camera device if the program requires webcam access for facial recognition.
- Please refer to the documentation for additional configuration options and usage instructions.

Enjoy using SecureFace for secure and reliable facial authentication! If you find any bugs or have suggestions for improvements, feel free to contribute or reach out to the project maintainers.