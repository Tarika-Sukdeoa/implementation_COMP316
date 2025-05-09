import subprocess
import threading


def run_streamlit():
    subprocess.run(["streamlit", "run", "app_api.py"])


def run_fastapi():
    subprocess.run(["uvicorn", "api:api", "--reload"])


if __name__ == "__main__":
    t1 = threading.Thread(target=run_streamlit)
    t2 = threading.Thread(target=run_fastapi)

    t1.start()
    t2.start()

    t1.join()
    t2.join()