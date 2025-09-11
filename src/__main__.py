import typer
from pathlib import Path
#import metrics, 

app = typer.Typer()

#Install necessary dependencies
@app.command()
def install():
    import subprocess
    
    print("Installing dependencies...")
    try:
        subprocess.run(["pip", "install", "--user", "-r", Path(__file__).parent.parent / "dependencies.txt"], check=True)
        print("Dependencies installed successfully.")
        raise typer.Exit(code=0)
    except subprocess.CalledProcessError:
        print(f"An error occurred while installing dependencies.")
        raise typer.Exit(code=1)
    
@app.command()
def test(): 
    import subprocess
    import sys
    print("Running tests...")
    test_dir = Path(__file__).parent / "tests"
    print("Done")

@app.command()
def URL_FILE(model_name: str, model_url: str, dataset_url: str, code_url: str,):
    print("Analyzing model...")
    
    print("Done")

if __name__ == "__main__":
    app()