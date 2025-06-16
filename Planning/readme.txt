def Google_API(query, wanted_row):
    """
    input : 
        query : str  검색하고 싶은 검색어 
        wanted_row : str 검색 결과를 몇 행 저장할 것인지 
    output : 
        df_google : dataframe / column = title, link,description  
        사용자로 부터 입력받은 쿼리문을 통해 나온 검색 결과를 wanted_row만큼 (100행을 입력받았으면) 100행이 저장된 데이터 프레임을 return합니다.
    """

    query= query.replace("|","OR") #쿼리에서 입력받은 | 기호를 OR 로 바꿉니다 
    query += "-filetype:pdf" # 검색식을 사용하여 file type이 pdf가 아닌 것을 제외시켰습니다 
    start_pages=[] # start_pages 라는 리스트를 생성합니다. 

    df_google= pd.DataFrame(columns=['Title','Link','Description']) # df_Google이라는 데이터 프레임에 컬럼명은 Title, Link, Description으로 설정했습니다.

    row_count =0 # dataframe에 정보가 입력되는 것을 카운트 하기 위해 만든 변수입니다. 


    for i in range(1,wanted_row+1000,10):
        start_pages.append(i) #구글 api는 1페이지당 10개의 결과물을 보여줘서 1,11,21순으로 로드한 페이지를 리스트에 담았습니다. 

    for start_page in start_pages:
      # 1페이지, 11페이지,21페이지 마다, 
        url = f"https://www.googleapis.com/customsearch/v1?key={Google_API_KEY}&cx={Google_SEARCH_ENGINE_ID}&q={query}&start={start_page}"
        # 요청할 URL에 사용자 정보인 API key, CSE ID를 저장합니다. 
        data = requests.get(url).json()
        # request를 requests 라이브러리를 통해서 요청하고, 결과를 json을 호출하여 데이터에 담습니다.
        search_items = data.get("items")
        # data의 하위에 items키로 저장돼있는 값을 불러옵니다. 
        # search_items엔 검색결과 [1~ 10]개의 아이템들이 담겨있다.  start_page = 11 ~ [11~20] 
        
        try:
          #try 구문을 하는 이유: 검색 결과가 null인 경우 link를 가져올 수가 없어서 없으면 없는대로 예외처리
            for i, search_item in enumerate(search_items, start=1):
              # link 가져오기 
                link = search_item.get("link")
                if any(trash in link for trash in Trash_Link):
                  # 링크에 dcinside, News 등을 포함하고 있으면 데이터를 데이터프레임에 담지 않고, 다음 검색결과로 
                    pass
                else: 
                    # 제목저장
                    title = search_item.get("title")
                    # 설명 저장 
                    descripiton = search_item.get("snippet")
                    # df_google에 한줄한줄 append 
                    df_google.loc[start_page + i] = [title,link,descripiton] 
                    # 저장하면 행 갯수 카운트 
                    row_count+=1
                    if (row_count >= wanted_row) or (row_count == 300) :
                      #원하는 갯수만큼 저장끝나면
                        return df_google
        except:
          # 더 이상 검색결과가 없으면 df_google 리턴 후 종료 
            return df_google

    
    return df_google
