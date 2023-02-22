def extractOverloadPeriod(log_txt, m, t):
    '''
    logからそれぞれのサーバーの過負荷期間を抽出
    過負荷状態に無かったサーバーに関しても空リストで出力
    ### input 
    以下のような形式のtxt
    20201019133124,10.20.30.1/16,2
    20201019133125,10.20.30.2/16,1
    ### return 
    サーバーと過負荷期間の辞書(サーバーアドレス:[過負荷開始日時, 過負荷解消日時])
    server_dict = {'10.20.30.1/16': [['20201019133324', '20201019133329'], ['20201019133424', '20201019133429']],
                   '10.20.30.2/16': [],
                   '192.168.1.2/24': [['20201019133324']]}
    ログ終了時点で過負荷状態のサーバーアドレスのリスト
    overload_server_lst = ['192.168.1.2/24']
    '''
    # 壊れた経験のあるサーバーの過負荷開始時間、過負荷終了時間を格納{address:[[begin, end],],}
    server_dict = {}
    # 直近m回のサーバーログを格納{address:[],}
    server_tmp_logs_dict = {}
    overload_server_lst = []
    # タイムアウトの応答時間仮定
    timeout = 300
    with open(log_txt) as logs:
        # 1行毎に処理をし過負荷期間を抽出
        for log in logs:
            date, address, result = log.split(',')
            result = result.rstrip('\n')

            if result == '-':
                result = timeout

            # server_dictへの登録
            if address not in server_dict: 
                server_dict[address] = []

            # overload_count_dictへの登録
            if address not in server_tmp_logs_dict:
                server_tmp_logs_dict[address] = []

            # overload_count_dictのデータ整形（m個以下のログを格納するため）
            server_tmp_logs_dict[address].append(float(result))
            if len(server_tmp_logs_dict[address]) > m:
                server_tmp_logs_dict[address] = server_tmp_logs_dict[address][1:]
            
            # 直近m回の平均応答時間の計算
            result_average = sum(server_tmp_logs_dict[address])/m

            if result_average >= t: # 過負荷の場合
                if address in overload_server_lst: # 既に過負荷の場合
                    continue
                else: # 過負荷開始の場合
                    # 過負荷開始日時を記録
                    overload_period_lst = server_dict[address]
                    overload_period_lst.append([date])
                overload_server_lst.append(address)
            
            else: # 過負荷ではない場合
                if address in overload_server_lst: # 過負荷だった場合
                    # 過負荷解消日時を記録
                    overload_period_lst = server_dict[address]
                    overload_period_lst[len(overload_period_lst)-1].append(date)
                    overload_server_lst.remove(address)

    return server_dict, overload_server_lst

def editOverloadPeriod(server_dict, overload_server_lst):
    '''
    extractOverloadPeriodで得たデータを出力形式に編集
    1. 過負荷していないサーバーの削除
    2. ping応答が帰って来ず、過負荷中の場合終了時刻を'inf'とする
    '''
    overload_server_dict = {}
    for address, overload_period_lst in server_dict.items():
        if address in overload_server_lst: # 未だ過負荷中の場合、末尾にinfを追加
            overload_period_lst[len(overload_period_lst) - 1].append('inf')
        if len(overload_period_lst): # 過負荷したことがある場合
            overload_server_dict[address] = overload_period_lst
    return overload_server_dict

def question3(log_txt, m, t):
    server_dict, overload_count_dict = extractOverloadPeriod(log_txt, m, t)
    server_dict = editOverloadPeriod(server_dict, overload_count_dict)
    with open('answer3.txt','wt') as f:
        f.write('address, brokenBegin, brokenEnd\n')
        for address, periods_lst in server_dict.items():
            for period in periods_lst:
                f.write(f'{address},{period[0]},{period[1]}\n')
if __name__ == '__main__':
    log = 'log.txt'
    m = 2
    t = 2
    print(question3(log, m, t))