def extractBrokenPeriod(log_txt):
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
    ログ終了時点で故障状態のサーバーアドレスのリスト
    broken_server_lst = ['192.168.1.2/24']
    '''
    # 壊れた経験のあるサーバーの故障開始時間、故障終了時間を格納
    server_dict = {}
    # 1行毎に処理していく中で故障状態のサーバーを格納し、故障が解消したら削除
    broken_server_lst = []
    with open(log_txt) as logs:
        # 1行毎に処理をし故障期間を抽出
        for log in logs:
            date, address, result = log.split(',')
            result = result.rstrip('\n')

            # server_dictへの登録
            if address not in server_dict: 
                server_dict[address] = []

            if result == '-': # タイムアウトの場合
                if address in broken_server_lst: # 既に故障中なら特に処理なし
                    continue
                else: # 故障開始の場合
                    # 故障開始日時を記録
                    broken_period_lst = server_dict[address]
                    broken_period_lst.append([date])
                    # 故障したのでリストに追加
                    broken_server_lst.append(address)
            
            else: # タイムアウトしていない場合
                if address in broken_server_lst: # 故障していたサーバーの場合
                    # 故障解消日時を記録
                    broken_period_lst = server_dict[address]
                    broken_period_lst[len(broken_period_lst)-1].append(date)
                    # 復旧したのでリストから削除
                    broken_server_lst.remove(address)
    return server_dict, broken_server_lst

def editBrokenPeriod(server_dict, broken_server_lst):
    '''
    extractBrokenPeriodで得たデータを出力形式に編集
    1. 故障していないサーバーの削除
    2. ping応答が帰って来ず、故障中の場合終了時刻を'inf'とする
    '''
    broken_server_dict = {}
    for address, broken_period_lst in server_dict.items():
        if address in broken_server_lst: # 未だ故障中の場合、末尾にinfを追加
            broken_period_lst[len(broken_period_lst) - 1].append('inf')
        if len(broken_period_lst): # 故障したことがある場合
            broken_server_dict[address] = broken_period_lst
    return broken_server_dict

def question1(log_txt):
    server_dict, broken_server_lst = extractBrokenPeriod(log_txt)
    server_dict = editBrokenPeriod(server_dict, broken_server_lst)
    # 結果を書き込む
    with open('answer1.txt','wt') as f:
        f.write('address, brokenBegin, brokenEnd\n')
        for address, periods_lst in server_dict.items():
            for period in periods_lst:
                f.write(f'{address},{period[0]},{period[1]}\n')

if __name__ == '__main__':
    log = 'log.txt'
    print(question1(log))

