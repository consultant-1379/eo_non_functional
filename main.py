"""
Start module
"""
import argparse
from lib.jobs import JOBS


def main():
    """
    Parse arguments and call operation
    """
    parser = argparse.ArgumentParser(description='Python CLI option parser')
    parser.add_argument('job', type=str, help='Option to execute a function')

    args = parser.parse_args()
    func = JOBS.get(args.job)

    if args.job in JOBS:
        func()
    else:
        helper()
        list_jobs()


def helper():
    """
    Helper function
    """
    print("---------------------------------------------")
    print("Automation script for non functional tests")
    print("Usage: python main.py 'job_name'")
    print("")
    print("---------------------------------------------")


def list_jobs():
    """
    List all available operations
    """
    print("Available jobs:")
    for job in JOBS:
        print(job)


if __name__ == '__main__':
    main()
