def extractBrokenPeriod(log_txt, N):
    '''
    logからそれぞれのサーバーの故障期間を抽出
    故障状態に無かったサーバーに関しても空リストで出力
    ### input 
    以下のような形式のtxt
    20201019133124,10.20.30.1/16,2
    20201019133125,10.20.30.2/16,1
    ### return 
    サーバーと故障期間の辞書(サーバーアドレス:[故障開始日時, 故障解消日時])
    server_dict = {'10.20.30.1/16': [['20201019133324', '20201019133329'], ['20201019133424', '20201019133429']],
                   '10.20.30.2/16': [],
                   '192.168.1.2/24': [['20201019133324']]}
    ログ終了時点でタイムアウト状態のサーバーアドレスの辞書(サーバーアドレス:連続タイムアウト回数)
    broken_count_dict = {'192.168.1.2/24':1, '10.20.30.1':0, '10.20.30.2':0}
    '''
    # 壊れた経験のあるサーバーの故障開始時間、故障終了時間を格納
    server_dict = {}
    # 1行毎に処理していく中で故障状態のサーバーを格納し、故障が解消したら削除
    broken_count_dict = {}
    with open(log_txt) as logs:
        # 1行毎に処理をし故障期間を抽出
        for log in logs:
            date, address, result = log.split(',')
            result = result.rstrip('\n')

            # server_dictへの登録
            if address not in server_dict: 
                server_dict[address] = []

            # broken_count_dictへの登録
            if address not in broken_count_dict:
                broken_count_dict[address] = 0
            
            if result == '-': # タイムアウトの場合
                # 連続タイムアウト回数を加算
                broken_count_dict[address] += 1
                if broken_count_dict[address] > 1: # 既に連続タイムアウトなら特に処理なし
                    continue
                else: # 連続タイムアウト開始の場合
                    # 連続タイムアウト開始日時を記録
                    broken_period_lst = server_dict[address]
                    broken_period_lst.append([date])
            
            else: # タイムアウトしていない場合
                if broken_count_dict[address] >= 1: # 故障していたサーバーの場合
                    broken_period_lst = server_dict[address]
                    if broken_count_dict[address] >= N: # 連続タイムアウト回数がN以上の場合
                        # 故障解消日時を記録
                        broken_period_lst[len(broken_period_lst)-1].append(date)
                    else: # 故障ではない場合
                        del broken_period_lst[-1]
                    # 復旧したのでカウントを0に
                    broken_count_dict[address] = 0

    return server_dict, broken_count_dict

def editBrokenPeriod(server_dict, broken_count_dict, N):
    '''
    extractBrokenPeriodで得たデータを出力形式に編集
    1. 故障していないサーバーの削除（最終ログ時点で連続N回未満のタイムアウトのサーバーも未故障扱い）
    2. 最終ログ時点で連続N回以上のタイムアウトがある場合、終了時刻を'inf'とする
    '''
    broken_server_dict = {}
    for address, broken_period_lst in server_dict.items():
        if broken_count_dict[address] >= N: # 未だ故障中の場合、末尾にinfを追加
            broken_period_lst[len(broken_period_lst) - 1].append('inf')
        elif N > broken_count_dict[address] > 0:# 最終ログ時点で連続N回未満のタイムアウトのサーバーも未故障扱い
            del broken_period_lst[-1]
        if len(broken_period_lst): # 故障したことがある場合
            broken_server_dict[address] = broken_period_lst
    return broken_server_dict

def question2(log_txt, N):
    server_dict, broken_count_dict = extractBrokenPeriod(log_txt, N)
    server_dict =  editBrokenPeriod(server_dict, broken_count_dict, N)
    # 結果を書き込む
    with open('answer2.txt','wt') as f:
        f.write('address, brokenBegin, brokenEnd\n')
        for address, periods_lst in server_dict.items():
            for period in periods_lst:
                f.write(f'{address},{period[0]},{period[1]}\n')
if __name__ == '__main__':
    log = 'log.txt'
    N = 2
    print(question2(log, N))