import csv
import os
from argparse import ArgumentParser

# merge file1 and file2 to final_file
# Requirement: both files contain the same header
def merge_two_csv_files(files, final_file):

    if os.path.exists(final_file):
        os.remove(final_file)

    with open(final_file, mode='w') as ff:
        writer = csv.writer(ff)

        # Process the first file
        with open(files[0], mode='r', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                writer.writerow(row)

        # Process the remaining files
        for file in files[1:]:
            with open(file, mode='r', newline='') as f:
                reader = csv.reader(f)
                next(reader)  # Skip the header row
                for row in reader:
                    writer.writerow(row)

def main(args):
    if args.files is None or args.final_file is None:
        print('Error: Please specify at least one input file and the final file')

    merge_two_csv_files(args.files, args.final_file)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--files', nargs='+',
                        help='Paths for input files', type=str, required=True)
    parser.add_argument('--final-file',
                        help='Path for final file', type=str, required=True)

    args = parser.parse_args()

    main(args)
