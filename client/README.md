# Local client deployment guide
1. Clone repo
```shell
git clone https://github.com/merirut/vcs.git
```

2. `cd` to the root folder of cloned directory
```shell
cd vcs
```

3. Create virtual environment (Python 3.9 has to be installed)
```shell
python -m venv venv
```
4. Activate virtual environment

    Linux/MacOS:
    
    ```shell
    . venv/bin/activate
    ```

    Windows:
    ```shell
   venv\Scripts\activate
   ```
5. Install dependencies
```shell
pip install -r requirements.txt
```


6. Run
```shell
python src/main.py
```