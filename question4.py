import ipaddress

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

def groupNet4(server_dict):
    '''
    サブネット内にあるネットワークを纏めて、出力
    ### input(使用はkeyのみ)
    server_dict = {'10.20.30.1/16': [['20201019133324', '20201019133329'], ['20201019133424', '20201019133429']],
                   '10.20.30.2/16': [],
                   '192.168.1.2/24': [['20201019133324']]}
    ### return
    net4_dict = {'10.20.0.0/16':['10.20.30.1/16', '10.20.30.2/16'],
                 '192.168.1.0/24':['192.168.1.2/24']}
    '''
    net4_dict = {}
    for address in server_dict.keys():
        # ネットワーク部
        net4 = str(ipaddress.ip_interface(address).network)
        if net4 in net4_dict:
            net4_dict[net4].append(address)
        else:
            net4_dict[net4] = [address]
    return net4_dict

def computeSeveralCoveredPeriod(periods_lst):
    '''
    複数要素の重複期間を計算
    ### input
    periods_lst = [[['20201019133220', '20201019133224'], ['20201019133324', '20201019133329'], ], 
                   [['20201019133222', '20201019133226'], ['20201019133324', '20201019133329'], ]]
    ### return
    base_periods_lst = [[20201019133222, 20201019133226], ]
    '''
    # 重複期間を比べる基準となる要素
    base_periods_lst = periods_lst[0]
    # その他の要素
    others_periods_lst = periods_lst[1:]
    # 2要素毎に重複期間を比較し、基準期間をその重複期間に更新する
    for other_periods_lst in others_periods_lst:
        base_periods_lst = computeCoveredPeriod(base_periods_lst, other_periods_lst)
        if not base_periods_lst:
            break
    
    return base_periods_lst

def computeCoveredPeriod(periods_lst_1, periods_lst_2):
    '''
    2つの要素の重複期間を計算
    ### input
    periods_lst_1 = [['20201019133220', '20201019133224'], ['20201019133324', '20201019133329'],]
    periods_lst_2 = [['20201019133222', '20201019133226'], ['20201019134324', '20201019134329'],]
    ### output
    covered_period_lst = [[20201019133222, 20201019133224],]
    '''

    covered_period_lst = []
    for period_1 in periods_lst_1:
        if len(period_1) == 0: # 期間無し
            break
        elif len(period_1) == 1: # 継続中（期間の終了時点を無限大に）
            begin_1 = float(period_1[0])
            end_1 = float('inf')
        else:
            begin_1, end_1 = list(map(float,period_1))
        
        for period_2 in periods_lst_2:
            if len(period_2) == 0: # 期間無し
                break
            elif len(period_2) == 1: # 継続中（期間の終了時点を無限大に）
                begin_2 = float(period_2[0])
                end_2 = float('inf')
            else:
                begin_2, end_2 = list(map(float,period_2))
            
            if not (begin_1 > end_2 or begin_2 > end_1): # 期間が重複していた場合
                # 重複期間をリストに格納
                covered_period_lst.append([max(begin_1, begin_2), min(end_1, end_2)])
    return covered_period_lst

def computeSubnetBrokenPeriod(server_dict):
    '''
    それぞれのサーバーの故障期間からサブネットの故障期間を計算
    ### input(使用はkeyのみ)
    server_dict = {'10.20.30.1/16': [['20201019133324', '20201019133329'], ['20201019133424', '20201019133429']],
                   '10.20.30.2/16': [],
                   '192.168.1.2/24': [['20201019133324']]}
    ### return
    subnet_dict = {'10.20.0.0/16': [],
                   '192.168.1.2/24': [[20201019133324, inf]]}
    '''
    subnet_dict = {}
    net4_dict = groupNet4(server_dict)
    for net4, host4_lst in net4_dict.items():
        periods_lst = []
        for host4 in host4_lst:
            # サブネット内のサーバーアドレスの故障期間をperiods_lstに格納
            periods_lst.append(server_dict[host4])
        # サブネットの故障期間を計算
        broken_periods_lst = computeSeveralCoveredPeriod(periods_lst)
        subnet_dict[net4] = broken_periods_lst
    return subnet_dict

def editSeverDict(server_dict, broken_count_dict, N):
    '''
    extractBrokenPeriodで得たデータでN回未満の連続タイムアウトを故障していないように編集
    '''
    broken_server_dict = {}
    for address, broken_period_lst in server_dict.items():
        if N > broken_count_dict[address] > 0:
            # 最終ログ時点で連続N回未満のタイムアウトのサーバーを未故障扱いに
            del broken_period_lst[-1]
        broken_server_dict[address] = broken_period_lst
    return broken_server_dict

def question4(log_txt, N):
    server_dict, broken_count_dict = extractBrokenPeriod(log_txt, N)
    server_dict = editSeverDict(server_dict, broken_count_dict, N)
    subnet_dict = computeSubnetBrokenPeriod(server_dict)
    # 結果を書き込む
    with open('answer4.txt','wt') as f:
        f.write('subnet, brokenBegin, brokenEnd\n')
        for address, periods_lst in subnet_dict.items():
            for period in periods_lst:
                period[0] = str(period[0]).replace('.0','')
                period[1] = str(period[1]).replace('.0','')
                f.write(f'{address},{period[0]},{period[1]}\n')

if __name__ == '__main__':
    log = 'log.txt'
    N = 2
    print(question4(log, N))
