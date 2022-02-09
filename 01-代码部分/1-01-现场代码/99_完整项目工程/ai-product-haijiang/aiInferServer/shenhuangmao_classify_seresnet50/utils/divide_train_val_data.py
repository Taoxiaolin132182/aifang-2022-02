import random
all_data_path = "./data/my_data/cotton_11_05_train_yx.txt"
train_data_path = "./data/my_data/cotton_11_05_train_yx_train.txt"
val_data_path = "./data/my_data/cotton_11_05_train_yx_val.txt"
all_data_lines = open(all_data_path).readlines()
train_data = open(train_data_path, "w")
val_data = open(val_data_path, "w")

factor = 0.9

all_num = len(all_data_lines)
train_data_num = int(factor*all_num)
all_data = random.shuffle(all_data_lines)
train_data_lines = all_data_lines[:train_data_num]
val_data_lines = all_data_lines[train_data_num:]

for line in train_data_lines:
    train_data.write(line)
train_data.close()

for line in val_data_lines:
    val_data.write(line)
val_data.close()



