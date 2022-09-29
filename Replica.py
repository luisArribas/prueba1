# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 13:43:17 2022

@author: luisr
"""

### Prueba en sucio para hacer todo
import pandas as pd
import requests
import json
import numpy as np
import time

##   Llamamos a las clases que hemos creado
import sys
sys.path.append("C:/Users/luisr/OneDrive/Desktop/MIAX/Practica Algos/")
import optimizador
import ApiHandler

url_base = 'https://miax-gateway-jog4ew3z3q-ew.a.run.app'
competi = 'mia_9'
user_key = 'AIzaSyCPQ1xbuluTctmf5ewKXEr8dBpz4s28S_Q'
market='DAX'
algo_tag = 'larribas_algo1'


##  Replicamos TICKER_MASTER
url = f'{url_base}/data/ticker_master'
params = {'competi': competi,
        'market': market,
        'key': user_key}
response = requests.get(url, params)
tk_master = response.json()
maestro_df = pd.DataFrame(tk_master['master'])

##  Replicamos GET_CLOSE_DATA
def get_close_data(market, tck):
    url = f'{url_base}/data/time_series'
    params = {
        'market': market,
        'key': user_key,
        'ticker': tck
    }
    response = requests.get(url, params)
    tk_data = response.json()
    series_data = pd.read_json(tk_data, typ='series')
    return series_data


##  Replicamos GET_DATA
data_close_dict = {}
ticker_master = maestro_df
for idx, row in ticker_master.iterrows():
    tck = row.ticker
    print(tck)
    close_data = get_close_data(market, tck)
    data_close_dict[tck] = close_data
df_close = pd.DataFrame(data_close_dict)

##  Creamos funcion para generar ventanas de rebalanceo y numero de datos que 
##  consideramos en cada ventana.
def window_generator(ventanas, periodos_rebalanceo, datos):
    # Generamos diccionario principal
    dict_ventana = {}
    
    ##  Iteramos para cada ventana
    for window in ventanas:
        dict_rebalanceo = {}
        
        ##  Iteramos para cada periodo de rebalanceo
        for rebal in periodos_rebalanceo:
            
            ##  Creamos los indices de las fechas en las que rebalanceamos
            rango_rebal = np.arange(window,datos.shape[0],rebal)
            
            ##  Si es necesario, alargamos el ultimo rango para no dejar una 
            ##  parte de la serie sin tratar
            if (datos.shape[0] - rango_rebal[-1]) < rebal:
                rango_rebal[-1] = datos.shape[0]
            #   Creamos lista para despues almacenar info
            lista = []
            
            ##  Iteramos para cada periodo de rebalanceo
            for i in rango_rebal: 
                
                ## Seleccionamos la ventana de datos para cada fecha de rebal
                datos_ventana = datos.iloc[i-window:i, :]
                
                ## Descartamos los activos que tengan algun dia sin precio 
                datos_ventana = datos_ventana.dropna(axis=1)
                
                ##  Calculamos rendimientos y matriz de covarianzas
                retornos = np.log(datos_ventana).diff().dropna().sum()
                cov_matrix = datos_ventana.cov()
                
                ##  Para el ultimo rango 
                if i == datos.shape[0]:
                    i = i-1
                    fecha_rebal = datos.index[i]
                
                ##  Guardamos cada fecha de rebalanceo    
                fecha_rebal = datos.index[i]
                
                ##  Creamos una tupla con fecha, rendimientos y matriz de cov
                lista.append((fecha_rebal,retornos,cov_matrix))
            
             ## Creamos un diccionario con los datos de todas las fechas rebal   
            dict_rebalanceo[rebal] = lista
         
        ##  Creamos un diccionario con los datos para todas las ventanas    
        dict_ventana[window] = dict_rebalanceo
        
    return(dict_ventana)

##  Definimos algunos periodos de rebalanceo y ventanas de datos para ver con
##  qué combinacion obtenemos mejores resultados
periodos_rebalanceo = [20]
ventanas = [20]
datos_ventanas = window_generator(ventanas, periodos_rebalanceo, df_close)

##  Ahora creamos una funcion que recorra este diccionario y aplique el optimizador
#def opt_function(datos_ventanas,ventanas,periodos_rebalanceo):
    
##  Llamamos a la clase
opt = optimizador.opt_portfolio()

results_w = {}
##  Bucle para las ventanas
for window in ventanas:
    print("ventana " + str(window))
    results_r = {}
    ##  Bucle para periodos de rebalanceo
    for rebal in periodos_rebalanceo:
        print("rebal " + str(rebal))
        results_f = {}
        ##  Bucle para cada una de las fechas
        for fecha in range(len(datos_ventanas[window][rebal])):
            print("fecha " + str(fecha))
            returns = datos_ventanas[window][rebal][fecha][1]
            cov_returns = datos_ventanas[window][rebal][fecha][2]
            try:
                pesos = opt.maximo_sharpe(returns,cov_returns)
                results_f[datos_ventanas[window][rebal][fecha][0]] = pesos
            except:
                pass
        results_r[rebal] = results_f
    results_w[window] = results_r

##  Ahora debemos aplicar el backtesting

##  Probamos para la combinacion 20-20
for fecha in results_w[20][20]:
    print(fecha)
    str_date = fecha.strftime('%Y-%m-%d')
    vec_pesos = results_w[20][20][fecha]

    df_intermedio = pd.Series(index=df_close.columns)
    df_intermedio[vec_pesos.index] = vec_pesos.values
    df_intermedio.fillna(0, inplace=True)
    vec_pesos = df_intermedio
    allocation = [

        {'ticker': tk, 'alloc': vec_pesos[tk]}
        for tk in vec_pesos.index
        ]

    ApiHandler.ApiHandler().send_alloc(algo_tag, market, str_date, allocation)

performace, trades = ApiHandler.ApiHandler().backtest_algo(algo_tag, market)   


##  Pasados 5 min
url = f'{url_base}/participants/algo_exec_results'
params = {
    'key': user_key,
    'competi': competi,
    'algo_tag': algo_tag,
    'market': market,
}


response = requests.get(url, params)
exec_data = response.json()
print(exec_data.get('status'))
print(exec_data.get('content'))
a = exec_data.get('content')
    
    #self.api_handler.delete_allocs(self.algo_tag, self.market)







algos = ApiHandler.ApiHandler().get_algos()




##  Para trabajar con la primera fecha
a = next(iter(results_w[20][20])) # outputs 'foo'
results_w[20][20][a]
str_date = a.strftime('%Y-%m-%d')

vec_pesos = results_w[20][20][a]
print(vec_pesos.values.sum())

if vec_pesos.values.sum() > 1:
    print("paramos")
    break



##  Leemos allocations
url = f'{url_base}/participants/algo_allocations'
params = {
    'key': user_key,
    'competi': competi,
    'algo_tag': algo_tag,
    'market': market,
}
response = requests.get(url, params)
df_allocs = ApiHandler.ApiHandler().allocs_to_frame(response.json())


import pandas as pd
import requests
import json
import numpy as np
import time

##   Llamamos a las clases que hemos creado
import sys
sys.path.append("C:/Users/luisr/OneDrive/Desktop/MIAX/Practica Algos/")
import optimizador
import ApiHandler
url_base = 'https://miax-gateway-jog4ew3z3q-ew.a.run.app'
competi = 'mia_9'
user_key = 'AIzaSyCPQ1xbuluTctmf5ewKXEr8dBpz4s28S_Q'
market='EUROSTOXX'
algo_tag = 'larribas_algo3'


##  Borramos allocations de una fecha
#def delete_allocs(self, algo_tag, market):

url = f'{url_base}/participants/delete_allocations'
url_auth = f'{url}?key={user_key}'
params = {
    'competi': competi,
    'algo_tag': algo_tag,
    'market': market,
    }
response = requests.post(url_auth, data=json.dumps(params))
print(response.text)



##  Lanzamos Backtesting
#♥def backtest_algo(self, algo_tag, market):
url = f'{url_base}/participants/exec_algo'
url_auth = f'{url}?key={user_key}'
params = {
    'competi': competi,
    'algo_tag': algo_tag,
    'market': market,
    }
response = requests.post(url_auth, data=json.dumps(params))
if response.status_code == 200:
    exec_data = response.json()
    status = exec_data.get('status')
    res_data = exec_data.get('content')
    if res_data:
        performace = pd.Series(res_data['result'])
        trades = pd.DataFrame(res_data['trades'])
        
else:
    exec_data = dict()
    print(response.text)




>>> a = [(1, u'abc'), (2, u'def')]
>>> [i[0] for i in a]









