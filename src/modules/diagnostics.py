import psutil
import logging
from datetime import datetime

logger = logging.getLogger("guardianOS")

def realizar_diagnostico():
    """Analisa CPU, RAM e Processos críticos."""
    print("\n🩺 Iniciando Diagnóstico de Performance...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "cpu_total": psutil.cpu_percent(interval=1),
        "ram_total": psutil.virtual_memory().percent,
        "viloes": []
    }

    # Identificar processos consumindo mais de 5% de CPU ou 500MB de RAM
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            cpu = proc.info['cpu_percent']
            ram_mb = proc.info['memory_info'].rss / (1024 * 1024)
            
            if cpu > 5.0 or ram_mb > 500:
                report["viloes"].append({
                    "nome": proc.info['name'],
                    "cpu": cpu,
                    "ram": ram_mb
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sugestões inteligentes
    print(f"\n📊 Status: CPU {report['cpu_total']}% | RAM {report['ram_total']}%")
    if report['ram_total'] > 80:
        print("⚠️  ALERTA: Memória RAM muito alta. Isso causa lentidão no navegador.")
    
    if report["viloes"]:
        print("\n🔥 Processos que mais consomem recursos:")
        for v in report["viloes"]:
            print(f" - {v['nome']} (CPU: {v['cpu']}% | RAM: {v['ram']:.0f} MB)")
            if "chrome" in v['nome'].lower() or "msedge" in v['nome'].lower():
                print("   💡 Dica: Muitas abas abertas detectadas. Considere suspender abas inativas.")
    
    return report