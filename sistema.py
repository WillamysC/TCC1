import CoolProp.CoolProp as CP

from funcoesUteis import *


fluid_list = ['R134a']
CP.set_reference_state(fluid_list[0] ,'ASHRAE')

# Unidades de medida
S_UNID = 'kJ/kg-K'
H_UNID = 'kJ/kg'
E_UNID = 'kW'

T_amb = 25 + 273.15 #K
T_L = -25 + 273.15
T_H = T_amb

T_cond = 40 + 273.15 #K
T_eva = -30 + 273.15 #K
Q_eva = 248.87*1000 #W


def computeProperties(fluid:str) -> dict[pd.DataFrame]:

    """PONTO 1"""
    h1 = CP.PropsSI('H', 'T', T_eva, 'Q', 1, fluid)
    P1 = CP.PropsSI('P', 'T', T_eva, 'Q', 1, fluid)
    s1 = CP.PropsSI('S', 'P', P1, 'H', h1, fluid)

    """PONTO 2s"""
    P2 = CP.PropsSI('P', 'T', 5+273.15, 'Q', 1, fluid)
    s2s = s1
    h2s = CP.PropsSI('H', 'P', P2, 'S', s2s, fluid)

    """PONTO 2"""
    eta_c = 0.85
    h2 = (h2s - h1)/eta_c + h1
    T2 = CP.PropsSI('T', 'H', h2, 'P', P2, fluid)
    s2 = CP.PropsSI('S', 'P', P2, 'H', h2, fluid)

    """PONTO 3"""
    P3 = P2 
    h3 = CP.PropsSI('H', 'P', P3, 'Q', 1, fluid)
    # P2 = CP.PropsSI('P', 'T', T_cond, 'Q', 0, fluid)
    s3 = CP.PropsSI('S', 'P', P3, 'H', h3, fluid)

    
    """PONTO 4s"""
    s4s = s3
    P4 = CP.PropsSI('P', 'T', T_cond, 'S', s4s, fluid)
    h4s = CP.PropsSI('H', 'P', P4, 'S', s4s, fluid)

    """PONTO 4"""
    h4 = (h4s - h3)/eta_c + h3
    s4 = CP.PropsSI('S', 'H', h4, 'P', P4, fluid)

    """PONTO 5"""
    P5 = P4
    # h5 = CP.PropsSI('H', 'T', T_cond, 'Q', 0, fluid)
    h5 = CP.PropsSI('H', 'P', P5, 'Q', 0, fluid)

    s5 = CP.PropsSI('S', 'H', h5, 'P', P5, fluid)

    """PONTO 6"""
    P6 = P2
    h6 = h5
    s6 = CP.PropsSI('S', 'H', h6, 'P', P6, fluid)
    
    """PONTO 7"""
    P7 = P2
    h7 = CP.PropsSI('H', 'T', 5+273.15, 'Q', 0, fluid)
    s7 = CP.PropsSI('S', 'P', P7, 'H', h7, fluid)

    """PONTO 8"""
    P8 = P1
    h8 = h7
    s8 = CP.PropsSI('S', 'P', P8, 'H', h8, fluid)


    """ANALISE DE ENERGIA"""
    m_bp = Q_eva/(h1 - h8)

    # m_bp*h3 + m_ap*h7 = m_ap*h4 + m_bp*h8 # equaão de balanço
    m_ap = m_bp*(h7 - h2s)/(h6 - h3)
    
    m1 = m2 = m7 = m8 = m_bp
    m3 = m4 = m5 = m6 = m_ap

    massas = [m1, m2, m3, m4, m5, m6, m7, m8]
    pressao = [P1, P2, P3, P4, P5, P6, P7, P8]
    entalpias = [h1, h2s, h3, h4s, h5, h6, h7, h8]
    entropias = [s1, s2s, s3, s4s, s5, s6, s7, s8]

    dfProps = propertiesDF(list(range(1,len(entalpias)+1)), massas, pressao, entalpias, entropias)

    Q_Con = m_ap*(h5 - h4s) #isentropico

    trocadoresCalor = pd.DataFrame({"Troc. de Calor":["evaporador", "condensador"],"Q (kW)": [Q_eva, Q_Con]})
    trocadoresCalor["Q (kW)"] = trocadoresCalor["Q (kW)"].div(1000)

    W_inB = W_ent(m_bp, h2s, h1) #isentropico
    W_inA = W_ent(m_ap, h4s, h3) #isentropico
    W_entr = W_inB + W_inA
    compressores = pd.DataFrame({"Compressoes":["compA", "compB"],"W_ent (kW)": [W_inA, W_inB]})
    compressores["W_ent (kW)"] = compressores["W_ent (kW)"].div(1000)

    COP = m_bp*(h1 - h8)/W_entr
    # print(f"COP: {COP:.3f}")

    """ANALISE DE EXERGIA"""

    """ANALISE DE EXERGIA (isentropica)"""
    # >>>>>>>>> BASEADO NO ARTIGO <<<<<<<<<<<
    ED_cbp = W_inB + deltaExergia(m_bp, h1, h2s, T_amb, s1, s2s) # Perda exergia no compressor de baixa pressao
    ED_cap = W_inA + deltaExergia(m_ap, h3, h4s, T_amb, s3, s4s) # Perda exergia no compressor de alta pressao

    ED_eva = deltaExergia(m_bp, h8, h1, T_amb, s8, s1) + Q_eva*(1 - T_amb/T_L)
    ED_cond = deltaExergia(m_ap, h4s, h5, T_amb, s4s, s5) - abs(Q_Con)*(1 - T_amb/T_H) 

    ED_veap = deltaExergia(m_ap, h5, h6, T_amb, s5, s6)
    ED_vebp = deltaExergia(m_bp, h7, h8, T_amb, s7, s8)

    ED_cf = deltaExergia(m_bp, h2s, h7, T_amb, s2s, s7) + deltaExergia(m_ap, h6, h3, T_amb, s6, s3) 

    ED_total_isen = ED_cap + ED_cbp + ED_eva + ED_cond + ED_veap + ED_vebp + ED_cf
    EDdf_isen = exergiaDF(ED_cap, ED_cbp, ED_eva, ED_cond, ED_veap, ED_vebp, ED_cf)

    # >>>>>>>>> BASEADO NO ÇENGEL  <<<<<<<<<<<
    """isentropico"""
    ED_cbp1 = m_bp*T_amb*(s2s - s1)
    ED_cap1 = m_ap*T_amb*(s4s - s3)
    ED_eva1 = T_amb*(m_bp*(s1 - s8) - Q_eva/T_L)
    ED_cond1 = T_amb*(m_ap*(s5 - s4s) + abs(Q_Con)/T_H)
    ED_veap1 = m_ap*T_amb*(s6 - s5)
    ED_vebp1 = m_bp*T_amb*(s8 - s7)
    ED_cf1 = T_amb*(m_bp*(s7 - s2s) + m_ap*(s3 - s6))

    ED_total1 = ED_cap1 + ED_cbp1 + ED_eva1 + ED_cond1 + ED_veap1 + ED_vebp1 + ED_cf1

    EDdf1 = exergiaDF(ED_cap1, ED_cbp1, ED_eva1, ED_cond1, ED_veap1, ED_vebp1, ED_cf1)

    eta_II = abs(Q_eva * (1 - T_amb/T_L))/W_entr

    eficiencia = pd.DataFrame({"COP": [COP], "Eta_II": [eta_II]})

    results = {
        "dfPropriedades": dfProps,
        "dfEficiencia": eficiencia.round(3),
        "dfTrocadoresCalor": trocadoresCalor.round(3),
        "dfCompressores": compressores.round(3),
        "dfExergiasDestruiadas": EDdf1.round(4)
        # "exergiasDestruiadas": EDdf.round(4)
        # "exergiasDestruiadas":EDdf_isen.round(4),
    }
    return results

     
#'CFC', 'HCFC', 'HFC', 'propyne'
fluids = ['R22','R134a', 'NH3', 'R744', '1BUTENE', 'R1233zd(E)', 'R1234yf', 'R1234ze(E)', 'R1243zf']

def computeResults(fluids:list[str]):
    
    result_dict={}

    for fluid in fluids:
        # CP.set_reference_state(fluid ,'ASHRAE')
        results = computeProperties(fluid)
        result_dict[fluid] = results

    return result_dict


results = computeResults(fluids)

def concat_df_by_chave(lista_chaves):
    dfs = {}
    
    for key, df_dict in results.items():
    
        try:
            for chave in lista_chaves:
                df = df_dict[chave]
                df["Refrigerante"] = key
                if chave in dfs:
                    dfs[chave].append(df)
                else:
                    dfs[chave] = [df]
        except Exception as e:
                    print(f"Error processing '{key}': {e}")
                    continue
            
    concatenated_dfs = {}
    for chave, df_list in dfs.items():
        concatenated_dfs[chave] = pd.concat(df_list, ignore_index=True)

    return concatenated_dfs

lista_chaves = ["dfPropriedades",
        "dfEficiencia",
        "dfTrocadoresCalor",
        "dfCompressores",
        "dfExergiasDestruiadas"]

concatenated_dfs = concat_df_by_chave(lista_chaves)

for i, df in concatenated_dfs.items():
    print(i, df) 