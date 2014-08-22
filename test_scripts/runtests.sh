#!/bin/bash
#
# test rftools on commandline level

root="`dirname $0`"/../bin
rfpack=$root/rfpack
rfunpack=$root/rfunpack
rfedit=$root/rfedit
rfformat=$root/rfformat
rfbuild=$root/rfbuild

test_filenames="`dirname $0`"/tests/files.txt					# List of free files to turn to fileseqs
shuffled_filenames="`dirname $0`"/tests/sort_test_shuffled.txt # filesequences messed up
ordered_filenames="`dirname $0`"/tests/sort_test_orig.txt		# ordered list of previous files
foreign_fileseqs="`dirname $0`"/tests/foreign_fileseqs.txt	# fileseq representation strings from filmlight, scratch etc.
local_fileseqs="`dirname $0`"/tests/local_fileseqs.txt		# foreign fileseqs should turn to these local fileseqs
build_dir="`dirname $0`"/"`mktemp -d tests/build.XXX`"
build_results="`dirname $0`"/tests/build_results.txt
temp="`dirname $0`"/"`mktemp tests/temp.XXX`"
trap finish exit

cmp_flags="-s"

function finish {
  # cleanup
  rm "$temp"
  if [ -d "$build_dir" ]; then
  	rm -rf "$build_dir"
  fi
}

function output {
	# Print out if last errorcode is ok or failed
	if [ ! $? -eq 0 ]; then
		echo "$1 ... FAILED!"
	else
		echo "$1 ... OK "
	fi
}

### Executables found and run ###
echo "==== Test executables ===="

$rfpack -h >/dev/null
if [ ! $? -eq 0 ]; then echo "$rfpack" fails; fi
$rfunpack -h >/dev/null
if [ ! $? -eq 0 ]; then echo "$rfunpack" fails; fi
$rfedit -h >/dev/null
if [ ! $? -eq 0 ]; then echo "$rfedit" fails; fi
$rfformat -h >/dev/null
if [ ! $? -eq 0 ]; then echo "$rfformat" fails; fi
$rfbuild -h >/dev/null
if [ ! $? -eq 0 ]; then echo "$rfbuild" fails; fi

# pack unpack filelist
echo -n "==== pack unpack $test_filenames ===="
cat "$test_filenames" | $rfpack -p | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames" "$temp"
output

# sort
echo -n "==== sort test ===="
cat "$shuffled_filenames" | $rfpack -n -s | $rfunpack > "$temp"
cmp $cmp_flags "$ordered_filenames" "$temp"
output

echo -n "==== invert test ===="
cat "$test_filenames" | $rfpack -1 -n -i | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_invert "$temp"
output

echo "==== edits ====" 
echo -n "---> trim 2 2"
cat "$test_filenames" | $rfpack -p -1 -n | $rfedit --trim 2 2 --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_trimmed "$temp"
output

echo -n "---> trim 00:02 00:02"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --trim 00:02 00:02 --fps 25 --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_tctrimmed "$temp"
output

echo -n "---> truncate 2 4"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --truncate 2 4 --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_truncated "$temp"
output

echo -n "---> head 3"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --head 3 --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_head "$temp"
output

echo -n "---> tail 00:02 --fps 25"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --tail 00:02 --fps 25 --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_tail "$temp"
output

echo -n "---> start -100"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --start -100 --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_start "$temp" 
output

echo -n "---> end 10:00:01:00 --fps 25"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --end "10:00:01:00" --fps 25 --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_end "$temp"
output

echo -n "---> basename start. .extension"
cat "$test_filenames" | $rfpack -p -1 -n | $rfedit --basename start. .extension --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_basename "$temp"
output

echo -n "---> reverse"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --reverse --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_reverse "$temp"
output

echo -n "---> padding 5"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --padding 5 --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_padding "$temp"
output

echo -n "---> reconstruct test.[0-100@@@@].dpx"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --reconstruct "test.[0-100@@@@].dpx" --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_reconstruct "$temp"
output

echo -n "---> removegaps"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --removegaps --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_removegaps "$temp"
output

echo -n "---> min 5"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --min 5 --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_min "$temp"
output

echo -n "---> max 5"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --max 5 --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_max "$temp"
output

echo -n "---> reorder 3 3 2 1"
cat "$test_filenames" | $rfpack -p -1 -n| $rfedit --reorder "3, 3, 2, 1" --single | $rfunpack > "$temp"
cmp $cmp_flags "$test_filenames"_reorder "$temp"
output

echo "==== format ===="
echo -n "---> output rv_style"
cat "$test_filenames" | $rfpack -p -1 -n| $rfformat -o "rv" > "$temp"
cmp $cmp_flags "$test_filenames"_format_rv "$temp"
output

echo -n "---> output printf"
cat "$test_filenames" | $rfpack -p -1 -n| $rfformat -o "printf" > "$temp"
cmp $cmp_flags "$test_filenames"_format_printf "$temp"
output

echo -n "---> output filmlight"
cat "$test_filenames" | $rfpack -p -1 -n| $rfformat -o "filmlight" > "$temp"
cmp $cmp_flags "$test_filenames"_format_filmlight "$temp"
output

echo "---> output free format"
echo -n "--> %F"
cat "$test_filenames" | $rfpack -p -1 -n| $rfformat -o "%F" > "$temp"
cmp $cmp_flags "$test_filenames"_format_fseqs "$temp"
output

echo -n "--> %f"
cat "$test_filenames" | $rfpack -p -1 -n| $rfformat -o "%f" > "$temp"
cmp $cmp_flags "$test_filenames"_format_fclips "$temp"
output

echo -n "--> %h %t %s %e %S %E %p %i %n %L %l %# %@"
cat "$test_filenames" | $rfpack -p -1 -n| $rfformat -o "%h %t %s %e %S %E %p %i %n %L %l %# %@" > "$temp"
cmp $cmp_flags "$test_filenames"_format_nontc "$temp"
output

echo -n "--> %F %< %> %- %= --fps 25 --tcstart 01:02"
cat "$test_filenames" | $rfpack -p -1 -n| $rfformat -o "%f %< %> %- %=" --fps 25 --tcstart 01:02 > "$temp"
cmp $cmp_flags "$test_filenames"_format_tc "$temp"
output

echo -n "---> input printf"
cat "$foreign_fileseqs"_printf | $rfformat -i printf > "$temp"
cmp $cmp_flags "$local_fileseqs" "$temp"
output

echo -n "---> input filmlight"
cat "$foreign_fileseqs"_filmlight | $rfformat -i filmlight > "$temp"
cmp $cmp_flags "$local_fileseqs" "$temp"
output

echo "==== rfbuild ===="
echo "---> create seqs"

mkdir -p "$build_dir"
"$rfbuild" test_seq_[-20-20@@@].dpx --cmd touch "$build_dir""/%modified" -x
"$rfbuild" moqs_[-20-20@].dpx --cmd touch "$build_dir""/%modified" -x

echo "---> offset moqs"
"$rfpack" -s -n "$build_dir"/moqs* | "$rfedit" --start 0 --padding 4 | "$rfbuild" --mv . -x

echo "---> copy test_seq"
"$rfpack" -s -n "$build_dir"/test_seq* | "$rfedit" --end 61 --padding 4 | "$rfbuild" --cp . -x

echo "---> sub clip"
"$rfpack" -s -n "$build_dir"/* | "$rfedit" --reconstruct "linked.[0-200@@@@].dpx" | "$rfbuild" --ln "$build_dir" -x

ls "$build_dir" | "$rfpack" -s -n > "$temp"
cmp $cmp_flags "$build_results" "$temp"
output "build test"
