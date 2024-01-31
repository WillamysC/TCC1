import CoolProp.CoolProp as CP

from funcoesUteis import *



fluid_list = ['R134a']
CP.set_reference_state(fluid_list[0] ,'ASHRAE')

# Unidades de medida
S_UNID = 'kJ/kg-K'
H_UNID = 'kJ/kg'
E_UNID = 'kW'

T_amb = 25 + 273.15 #K
T_cond = 40 + 273.15 #K
T_eva = -20 + 273.15 #K
Q_eva = 12000 #W


def computeProperties(fluid:list[str]) -> dict[pd.DataFrame]:

    """PONTO 1"""
    h1 = CP.PropsSI('H', 'T', T_eva, 'Q', 1, fluid_list[0])
    P1 = CP.PropsSI('P', 'T', T_eva, 'Q', 1, fluid_list[0])
    s1 = CP.PropsSI('S', 'P', P1, 'H', h1, fluid_list[0])

    """PONTO 2s"""
    P2 = CP.PropsSI('P', 'T', 5+273.15, 'Q', 1, fluid_list[0])
    s2s = s1
    h2s = CP.PropsSI('H', 'P', P2, 'S', s2s, fluid_list[0])

    """PONTO 2"""
    eta_c = 0.85
    h2 = (h2s - h1)/eta_c + h1
    # h2 = CP.PropsSI('H', 'T', 5+273.15, 'Q', 1, fluid_list[0])
    # P2 = CP.PropsSI('P', 'T', 5+273.15, 'Q', 1, fluid_list[0])
    T2 = CP.PropsSI('T', 'H', h2, 'P', P2, fluid_list[0])
    # print(T)
    # T2 = CP.PropsSI('T', 'S', s2s, 'Q', 1, fluid_list[0])
    s2 = CP.PropsSI('S', 'P', P2, 'H', h2, fluid_list[0])

    """PONTO 3"""
    P3 = P2
    h3 = CP.PropsSI('H', 'P', P3, 'Q', 1, fluid_list[0])
    # P2 = CP.PropsSI('P', 'T', T_cond, 'Q', 0, fluid_list[0])
    s3 = CP.PropsSI('S', 'P', P3, 'H', h3, fluid_list[0])

    """PONTO 4"""
    h4 = h3
    P4 = P3
    s4 = CP.PropsSI('S', 'P', P2, 'H', h4, fluid_list[0])

    T4 = CP.PropsSI('T', 'H', h4, 'P', P4, fluid_list[0])
    # print(T)
    
    """PONTO 5s"""
    P5 = CP.PropsSI('P', 'T', T_cond, 'Q', 1, fluid_list[0])
    s5s = s4
    h5s = CP.PropsSI('H', 'P', P5, 'S', s5s, fluid_list[0])

    """PONTO 5"""
    h5 = (h5s - h4)/eta_c + h4
    # h5 = CP.PropsSI('H', 'T', T_cond, 'Q', 1, fluid_list[0])
    # P5 = CP.PropsSI('P', 'T', T_cond, 'Q', 1, fluid_list[0])
    s5 = CP.PropsSI('S', 'H', h5, 'P', P5, fluid_list[0])

    """PONTO 6"""
    P6 = P5
    h6 = CP.PropsSI('H', 'T', T_cond, 'Q', 0, fluid_list[0])
    s6 = CP.PropsSI('S', 'H', h6, 'P', P6, fluid_list[0])

    """PONTO 7"""
    P7 = P2
    h7 = h6
    s7 = CP.PropsSI('S', 'H', h7, 'P', P7, fluid_list[0])
    
    """PONTO 8"""
    P8 = P2
    h8 = CP.PropsSI('H', 'T', 5+273.15, 'Q', 0, fluid_list[0])
    s8 = CP.PropsSI('S', 'P', P8, 'H', h8, fluid_list[0])

    """PONTO 9"""
    P9 = P1
    h9 = h8
    # h9 = CP.PropsSI('H', 'P', P9, 'T', T_eva, fluid_list[0])
    s9 = CP.PropsSI('S', 'P', P9, 'H', h9, fluid_list[0])

    # print("entalpia isentropica em 2: ", h2s)
    # print("entalpia isentropica em 5: ", h5s)
    
    # print("s2s: ", s2s)
    # print("s5s: ", s5s)


    """ANALISE DE ENERGIA"""
    m_bp = Q_eva/(h1 - h9)

    # m_bp*h3 + m_ap*h7 = m_ap*h4 + m_bp*h8 # equaão de balanço
    m_ap = m_bp*(h8 - h3)/(h7 - h4)
    
    m1 = m2 = m3 = m8 = m9 = m_bp
    m4 = m5 = m6 = m7 = m_ap
    Q_Con = m_ap*(h6 - h5)
    # Q_Con = m_ap*(h6 - h5s) #isentropico

    trocadoresCalor = pd.DataFrame({"Q (kW)": [Q_eva, Q_Con]}, index=["evaporador", "condensador"]).div(1000)


    W_inB = W_ent(m_bp, h2, h1)
    W_inA = W_ent(m_ap, h5, h4)
    # W_inB = W_ent(m_bp, h2s, h1) #isentropico
    # W_inA = W_ent(m_ap, h5s, h4) #isentropico
    W_entr = W_inB + W_inA
    compressores = pd.DataFrame({"W_ent (kW)": [W_inA, W_inB, W_entr]}, index=["compA", "compB", "Total"]).div(1000)

    COP = m_bp*(h1 - h9)/W_entr
    print(f"COP: {COP:.3f}")

    """ANALISE DE EXERGIA"""
    # >>>>>>>>> BASEADO NO ARTIGO <<<<<<<<<<<
    ED_cbp = W_inB + deltaExergia(m_bp, h1, h2, T_amb, s1, s2) # Perda exergia no compressor de baixa pressao
    ED_cap = W_inA + deltaExergia(m_ap, h4, h5, T_amb, s4, s5) # Perda exergia no compressor de alta pressao

    ED_eva = deltaExergia(m_bp, h9, h1, T_amb, s9, s1) + Q_eva*(1 - T_amb/T_eva)
    ED_cond = deltaExergia(m_ap, h5, h6, T_amb, s5, s6) - abs(Q_Con)*(1 - T_amb/T_cond) 

    ED_veap = deltaExergia(m_ap, h6, h7, T_amb, s6, s7)
    ED_vebp = deltaExergia(m_bp, h8, h9, T_amb, s8, s9)

    ED_wi = deltaExergia(m_bp, h2, h3, T_amb, s2, s3)

    ED_cf = deltaExergia(m_bp, h3, h8, T_amb, s3, s8) + deltaExergia(m_ap, h7, h4, T_amb, s7, s4) 

    ED_total = ED_cap + ED_cbp + ED_eva + ED_cond + ED_veap + ED_vebp + ED_wi + ED_cf
    print
    EDdf = exergiaDF(ED_cap, ED_cbp, ED_eva, ED_cond, ED_veap, ED_vebp, ED_wi, ED_cf)

    """ANALISE DE EXERGIA (isentropica)"""
    # >>>>>>>>> BASEADO NO ARTIGO <<<<<<<<<<<
    # ED_cbp = W_inB + deltaExergia(m_bp, h1, h2s, T_amb, s1, s2s) # Perda exergia no compressor de baixa pressao
    # ED_cap = W_inA + deltaExergia(m_ap, h4, h5s, T_amb, s4, s5s) # Perda exergia no compressor de alta pressao

    # ED_eva = deltaExergia(m_bp, h9, h1, T_amb, s9, s1) + Q_eva*(1 - T_amb/T_eva)
    # ED_cond = deltaExergia(m_ap, h5s, h6, T_amb, s5s, s6) - abs(Q_Con)*(1 - T_amb/T_cond) 

    # ED_veap = deltaExergia(m_ap, h6, h7, T_amb, s6, s7)
    # ED_vebp = deltaExergia(m_bp, h8, h9, T_amb, s8, s9)

    # ED_wi = deltaExergia(m_bp, h2s, h3, T_amb, s2s, s3)
    # # ED_wi_ = Ex(m_bp,h2,  )

    # ED_cf = deltaExergia(m_bp, h3, h8, T_amb, s3, s8) + deltaExergia(m_ap, h7, h4, T_amb, s7, s4) 

    # ED_total_isen = ED_cap + ED_cbp + ED_eva + ED_cond + ED_veap + ED_vebp + ED_wi + ED_cf
    # print
    # EDdf_isen = exergiaDF(ED_cap, ED_cbp, ED_eva, ED_cond, ED_veap, ED_vebp, ED_wi, ED_cf)

    # >>>>>>>>> BASEADO NO ÇENGEL  <<<<<<<<<<<
    """isentropico"""
    # ED_cbp1 = m_bp*T_amb*(s2s - s1)
    # ED_cap1 = m_ap*T_amb*(s5s - s4)
    # ED_eva1 = T_amb*(m_bp*(s1 - s9) - Q_eva/T_eva)
    # ED_cond1 = T_amb*(m_ap*(s6 - s5s) + abs(Q_Con)/T_cond)
    # ED_veap1 = m_ap*T_amb*(s7 - s6)
    # ED_vebp1 = m_bp*T_amb*(s9 - s8)
    # ED_wi1 = m_bp*T_amb*(s3 - s2s)
    # ED_cf1 = T_amb*(m_ap*(s7 - s6) + m_bp*(s9 - s8))

    """normal"""
    ED_cbp1 = m_bp*T_amb*(s2 - s1)
    ED_cap1 = m_ap*T_amb*(s5 - s4)
    ED_eva1 = T_amb*(m_bp*(s1 - s9) - Q_eva/T_eva)
    ED_cond1 = T_amb*(m_ap*(s6 - s5) + abs(Q_Con)/T_cond)
    ED_veap1 = m_ap*T_amb*(s7 - s6)
    ED_vebp1 = m_bp*T_amb*(s9 - s8)
    ED_wi1 = m_bp*T_amb*(s3 - s2)
    ED_cf1 = T_amb*(m_ap*(s7 - s6) + m_bp*(s9 - s8))

    # print(T_amb*m_bp*(s1 - s9), T_amb*Q_eva/T_eva)
    # print(T_amb*m_ap*(s6 - s5s), T_amb*abs(Q_Con)/T_cond)
    # print(W_entr - Q_eva*(T_amb - T_eva)/T_eva)

    ED_total1 = ED_cap1 + ED_cbp1 + ED_eva1 + ED_cond1 + ED_veap1 + ED_vebp1 + ED_wi1 + ED_cf1
    EDdf1 = exergiaDF(ED_cap1, ED_cbp1, ED_eva1, ED_cond1, ED_veap1, ED_vebp1, ED_wi1, ED_cf1)
    # print(ED_total1)


    massas = [m1, m2, m3, m4, m5, m6, m7, m8, m9]
    pressao = [P1, P2, P3, P4, P5, P6, P7, P8, P9]
    entalpias = [h1, h2s, h3, h4, h5s, h6, h7, h8, h9]
    entropias = [s1, s2s, s3, s4, s5s, s6, s7, s8, s9]

    dfProps = propertiesDF(list(range(1,len(entalpias)+1)), massas, pressao, entalpias, entropias)

    results = {
        "dfProps": dfProps,
        "trocadoresCalor": trocadoresCalor.round(2),
        "compressores": compressores.round(2),
        "exergiasDestruiadas1": EDdf1.round(4),
        "exergiasDestruiadas": EDdf.round(4)
    }
    return results

     
results = computeProperties(fluid_list)


for key, df in results.items():
    # print(key)
    print(df)