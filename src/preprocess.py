import argparse
import numpy as np
import os

RATING_FILE_NAME = dict(
    {'movie': 'ratings.dat', 'book': 'BX-Book-Ratings.csv', 'news': 'ratings.txt', 'recommend': 'ratings.dat'})
SEP = dict({'movie': '::', 'book': ';', 'news': '\t', 'recommend': '::'})
THRESHOLD = dict({'movie': 4, 'book': 0, 'news': 0, 'recommend': 4})


def read_item_index_to_entity_id_file():
    file = '../data/' + DATASET + '/item_index2entity_id.txt'
    print('Reading item index to entity id file: ' + file + '...')
    i = 0
    for line in open(file, encoding='utf-8').readlines():
        item_index = line.strip().split('\t')[0]
        satori_id = line.strip().split('\t')[1]
        item_index_old2new[item_index] = i
        entity_id2index[satori_id] = i
        i += 1


def convert_rating():
    file = '../data/' + DATASET + '/' + RATING_FILE_NAME[DATASET]

    print('Reading rating file...')
    item_set = set(item_index_old2new.values())
    user_pos_ratings = dict()
    user_neg_ratings = dict()

    for line in open(file, encoding='utf-8').readlines()[1:]:
        array = line.strip().split(SEP[DATASET])

        # remove prefix and suffix quotation marks for BX dataset
        if DATASET == 'book':
            array = list(map(lambda x: x[1:-1], array))

        item_index_old = array[1]
        if item_index_old not in item_index_old2new:  # the item is not in the final item set
            continue
        item_index = item_index_old2new[item_index_old]

        user_index_old = int(array[0])

        rating = float(array[2])
        if rating >= THRESHOLD[DATASET]:
            if user_index_old not in user_pos_ratings:
                user_pos_ratings[user_index_old] = set()
            user_pos_ratings[user_index_old].add(item_index)
        else:
            if user_index_old not in user_neg_ratings:
                user_neg_ratings[user_index_old] = set()
            user_neg_ratings[user_index_old].add(item_index)

    print('Converting rating file...')
    writer = open('../data/' + DATASET + '/ratings_final.txt', 'w', encoding='utf-8')
    user_cnt = 0
    for user_index_old, pos_item_set in user_pos_ratings.items():
        print(user_index_old, end='\r')
        if user_index_old not in user_index_old2new:
            user_index_old2new[user_index_old] = user_cnt
            user_cnt += 1
        user_index = user_index_old2new[user_index_old]

        for item in pos_item_set:
            writer.write('%d\t%d\t1\n' % (user_index, item))
        unwatched_set = item_set - pos_item_set
        if user_index_old in user_neg_ratings:
            unwatched_set -= user_neg_ratings[user_index_old]
        for item in np.random.choice(list(unwatched_set), size=len(pos_item_set), replace=False):
            writer.write('%d\t%d\t0\n' % (user_index, item))
    writer.close()
    print('Number of users: %d' % user_cnt)
    print('Number of items: %d' % len(item_set))


def convert_test():
    file = '../data/' + DATASET + '/test.dat'

    print('Converting test data file...')

    writer = open('../data/' + DATASET + '/test_final.txt', 'w', encoding='utf-8')
    neg_writer = open('../data/' + DATASET + '/neg_list.txt', 'w', encoding='utf-8')

    item_index_not_found = 0
    user_index_not_found = 0

    for line in open(file, encoding='utf-8').readlines():
        array = line.strip().split(SEP[DATASET])

        item_index_old = array[1]
        if item_index_old not in item_index_old2new:  # the item is not in the final item set
            neg_writer.write(line.strip() + '::ITEM\n')
            item_index_not_found += 1
            continue
        item_index = item_index_old2new[item_index_old]
        user_index_old = int(array[0])
        if user_index_old not in user_index_old2new:
            neg_writer.write(line.strip() + '::USER\n')
            user_index_not_found += 1
            continue
        user_index = user_index_old2new[user_index_old]
        writer.write('%d\t%d\t1\n' % (user_index, item_index))

    print('Item index not found:', item_index_not_found)
    print('User index not found:', user_index_not_found)

    writer.close()
    neg_writer.close()


def convert_kg():
    print('Converting kg file ...')
    entity_cnt = len(entity_id2index)
    relation_cnt = 0

    writer = open('../data/' + DATASET + '/kg_final.txt', 'w', encoding='utf-8')

    files = []
    if DATASET == 'movie':
        files.append(open('../data/' + DATASET + '/kg_part1.txt', encoding='utf-8'))
        files.append(open('../data/' + DATASET + '/kg_part2.txt', encoding='utf-8'))
        # files.append(open('../data/' + DATASET + '/kg.txt', encoding='utf-8'))
    else:
        files.append(open('../data/' + DATASET + '/kg.txt', encoding='utf-8'))

    for file in files:
        for line in file:
            array = line.strip().split('\t')
            head_old = array[0]
            relation_old = array[1]
            tail_old = array[2]

            if head_old not in entity_id2index:
                entity_id2index[head_old] = entity_cnt
                entity_cnt += 1
            head = entity_id2index[head_old]

            if tail_old not in entity_id2index:
                entity_id2index[tail_old] = entity_cnt
                entity_cnt += 1
            tail = entity_id2index[tail_old]

            if relation_old not in relation_id2index:
                relation_id2index[relation_old] = relation_cnt
                relation_cnt += 1
            relation = relation_id2index[relation_old]

            writer.write('%d\t%d\t%d\n' % (head, relation, tail))

    writer.close()
    print('Number of entities (containing items): %d' % entity_cnt)
    print('Number of relations: %d' % relation_cnt)


def persistence():
    print('Persist all index files...')

    index_path = '../data/' + DATASET + '/index'
    if not os.path.isdir(index_path):
        os.mkdir(index_path)

    with open(index_path + '/entity_id2index.txt', 'w', encoding='utf-8') as f:
        for key, value in entity_id2index.items():
            print(str(key) + '\t' + str(value), file=f)
    with open(index_path + '/relation_id2index.txt', 'w', encoding='utf-8') as f:
        for key, value in relation_id2index.items():
            print(str(key) + '\t' + str(value), file=f)
    with open(index_path + '/item_index_old2new.txt', 'w', encoding='utf-8') as f:
        for key, value in item_index_old2new.items():
            print(str(key) + '\t' + str(value), file=f)
    with open(index_path + '/user_index_old2new.txt', 'w', encoding='utf-8') as f:
        for key, value in user_index_old2new.items():
            print(str(key) + '\t' + str(value), file=f)


if __name__ == '__main__':

    print('NOTE: After running preprocess.py, delete *.npy in ./data folder.')

    np.random.seed(555)

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', type=str, default='movie', help='which dataset to preprocess')
    args = parser.parse_args()
    DATASET = args.d

    entity_id2index = dict()
    relation_id2index = dict()
    item_index_old2new = dict()
    user_index_old2new = dict()

    read_item_index_to_entity_id_file()
    convert_rating()
    convert_test()
    convert_kg()

    persistence()

    print('Done.')
