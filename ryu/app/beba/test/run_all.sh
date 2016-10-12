declare -A ret_values

for f in *.py;
do
	if [[ $f == *"__ryu.py"* ]]
	then
	  continue
	fi
	echo -e "\n\x1b[33m[Testing $f]\x1b[0m";
	if [ "$1" == "verbose" ]; then
		sudo python $f verbose;
	else
		sudo python $f;
	fi
	ret_values[$f]=$?;
done

for f in *__ryu.py;
do
	echo -e "\n\x1b[33m[Testing $f]\x1b[0m";
	if [ "$1" == "verbose" ]; then
		verbose = "true";
		sudo ryu-manager --verbose $f;
	else
		sudo ryu-manager $f;
	fi
	ret_values[$f]=$?;
done 

echo -e "\n*******************************************************************\n\nSUMMARY:\n"

for f in *.py;
do
	if [[ $f == *"__ryu.py"* ]]
	then
	  continue
	fi
	if [[ ${ret_values[$f]} -eq 1 ]]; then
		echo -e "$f: \x1b[31mFAILED\x1b[0m";
	else
		echo -e "$f: \x1b[32mSUCCEEDED\x1b[0m";
	fi
done

for f in *__ryu.py;
do
	if [[ ${ret_values[$f]} -eq 137 ]]; then
		echo -e "$f: \x1b[31mFAILED\x1b[0m";
	else
		echo -e "$f: \x1b[32mSUCCEEDED\x1b[0m";
	fi
done

# If any of the test has failed, we need to return -1
for f in *.py;
do
        if [[ $f == *"__ryu.py"* ]]
        then
          continue
        fi
        if [[ ${ret_values[$f]} -eq 1 ]]; then
                exit -1
        fi
done

for f in *__ryu.py;
do
        if [[ ${ret_values[$f]} -eq 137 ]]; then
                exit -1
        fi
done
