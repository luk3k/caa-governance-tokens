import csv
import os
from argparse import ArgumentParser

# merge file1 and file2 to final_file
# Requirement: both files contain the same header
def merge_two_csv_files(file1, file2, final_file):

    if os.path.exists(final_file):
        os.remove(final_file)

    with open(final_file, mode='w') as ff:
        writer = csv.writer(ff)

        with open(file1, mode='r') as f1:
            reader = csv.reader(f1)
            for row in reader:
                writer.writerow(row)

        with open(file2, mode='r') as f2:
            reader = csv.reader(f2)
            next(reader)  # Skip the first row
            for row in reader:
                writer.writerow(row)

def main(args):
    if args.file1 is None or args.file2 is None or args.final_file is None:
        print('Error: Please specify file1, file2 and final_file')

    merge_two_csv_files(args.file1, args.file2, args.final_file)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--file1',
                        help='Path for file 1', type=str, required=True)
    parser.add_argument('--file2',
                        help='Path for file 2', type=str, required=True)
    parser.add_argument('--final_file',
                        help='Path for final file', type=str, required=True)

    args = parser.parse_args()

    main(args)
