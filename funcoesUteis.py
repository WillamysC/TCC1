import pandas as pd
import CoolProp.CoolProp as CP

MIL = 1000

def propertiesDF(pontos: list[int], m: list[float], p: list[float], h: list[float], s: list[float]) -> pd.DataFrame:
    columns = {"fluxo m (kg/s)": m,
               "Pressão (Pa)": p,
               "Entalpia (kJ/kg)": h,
               "Entropia (kJ/kg-K)": s}
    df = pd.DataFrame(columns, index=pontos)
    df["fluxo m (kg/s)"] = df["fluxo m (kg/s)"].round(4)
    df["Pressão (Pa)"] = df["Pressão (Pa)"].round(2)
    df["Entalpia (kJ/kg)"] = df["Entalpia (kJ/kg)"].div(MIL).round(2)
    df["Entropia (kJ/kg-K)"] = df["Entropia (kJ/kg-K)"].div(MIL).round(4)

    return df

def exergiaDF(ED_cap, ED_cbp, ED_eva, ED_cond, ED_veap, ED_vebp, ED_wi, ED_cf)->pd.DataFrame:
    columns = {
        "comp": ["Compressor A", "Compressor B", "Evaporador", "Condensador", "Valvula A", "Valvula B", "Intercooler", "Camara Flash"],
        "ED (kW)": [ED_cap, ED_cbp, ED_eva, ED_cond, ED_veap, ED_vebp, ED_wi, ED_cf]
    }
    df = pd.DataFrame(columns)
    df["ED (kW)"] = df["ED (kW)"].div(1000)
    return df

def titulo(h_i, P_i, fluido) -> float:
    """
    h_i: entalpia do ponto de analise
    P_i: pressão do ponto de analise
    fluido: fluido utilizado
    """
    hl = CP.PropsSI('H', 'P', P_i, 'Q', 0, fluido)
    hv = CP.PropsSI('H', 'P', P_i, 'Q', 1, fluido)

    return (h_i - hl)/(hv - hl)

def deltaExergia(m_dot, h_in, h_out, T_amb, s_in, s_out):
    return m_dot*((h_in - h_out) - T_amb*(s_in - s_out))

def Ex(m_dot, h, h_amb,T_amb, s, s_amb):
    return m_dot*((h - h_amb) - T_amb*(s - s_amb))

def S_ger(m_dot, s_in, s_out):
    """
    Calculo da exergia:
    """
    return m_dot*(s_out - s_in)

def Temp_C_to_K(T_Celcius):
    return T_Celcius + 273

def Q_l(m_dot, h_sai, h_entr) -> float:
    return m_dot * (h_sai - h_entr)

def W_ent(m_dot, h_sai, h_entr) -> float:
    return m_dot * (h_sai - h_entr)

def Q_h(m_dot, h_entr, h_sai) -> float:
    return m_dot * (h_entr - h_sai)