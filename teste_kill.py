from database import salvar_kill, get_connection

def testar():
    print("🧹 Limpando banco para remover erros antigos...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kills")
    conn.commit()
    conn.close()

    print("🚀 Injetando dados de teste...")
    # Casos que DEVEM aparecer
    salvar_kill("[A.V.G]HsNighHell", "Inimigo_Bob", "AK-47", "150m")
    salvar_kill("[A.V.G]Davi", "Inimigo_Bob", "M4A1", 50)
    
    # Caso onde AVG morre (Deve contar morte para Davi, mas o Inimigo não aparece no ranking)
    salvar_kill("Inimigo_Sniper", "$ Davi", "AWM", "400m")
    salvar_kill("Inimigo_Sniper", "Davi", "AWM", "400m")

    print("✅ Sucesso! Agora abra o site.")

if __name__ == "__main__":
    testar()