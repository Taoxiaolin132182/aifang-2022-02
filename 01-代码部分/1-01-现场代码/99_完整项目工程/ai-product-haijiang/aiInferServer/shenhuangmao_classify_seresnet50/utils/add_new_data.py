
new_data_path = "./data/my_data/cotton_11_05_train_yx.txt"
old_data_path = "./data/my_data/cotton_11_05_train_yx.txt"
combine_data_path = "./data/my_data/cotton_11_05_train_yx_combine_test.txt"
new_data = open(new_data_path).readlines()
old_data = open(old_data_path).readlines()
combine_data = open(combine_data_path, "w")

combine_data_lines = new_data + old_data
for line in combine_data_lines:
    combine_data.write(line)
combine_data.close()


