import os
import sys

OUT_RESULTS_DIR = "./results"

# out_prefix is the prefix of the file to write (INCLUDING THE DIRECTORY). The
# output file will have the format [out_prefix]_[file_number]. The infile_name
# is the input file to read (INCLUDING THE DIRECTORY)
def split_into_files(out_prefix, infile_name):
    with open(infile_name, 'rb') as infile:
        file_number = 0
        outfile_name = out_prefix + "_" + str(file_number)
        outfile = open(outfile_name, 'wb')
        for line in infile:
            if len(line) <= 1:
                file_number += 1
                outfile.close()
                outfile_name = out_prefix + "_" + str(file_number)
                outfile = open(outfile_name, 'wb')
                continue
            outfile.write(line)
        outfile.close()

# filename is the name of the individual file, indir_name is the name of the
# input directory (so that we can open the file), and outdir_name is the
# name of the output directory, so we can write the output files
def split_single_file(file_path, outdir_name, outfile_prefix = None):
    filename = file_path[file_path.rfind('/')+1:]
    if outfile_prefix is None:
        outfile_prefix = filename[:filename.rfind('_')]
    outfile_path = outdir_name + "/" + outfile_prefix
    split_into_files(outfile_path, file_path)

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print "ERROR: Too few arguments: Expecting filename"
        sys.exit(-1)

    file_to_split = sys.argv[1]
    if len(sys.argv) <= 2:
        split_single_file(file_to_split, OUT_RESULTS_DIR)
    else:
        split_single_file(file_to_split, OUT_RESULTS_DIR, sys.argv[2])
