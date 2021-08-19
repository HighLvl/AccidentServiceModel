import model


def do_test(file_path, optimal_node):
    stat = model.run_model(file_path, test_mode=True)

    assert optimal_node == stat[0][0]


def test_test1_txt():
    do_test("test1.txt", 3)

def test_test2_txt():
    do_test("test2.txt", 7)

def test_test3_txt():
    do_test("test3.txt", 5)

def test_test4_txt():
    do_test("test4.txt", 7)

def test_test5_txt():
    do_test("test5.txt", 7)
