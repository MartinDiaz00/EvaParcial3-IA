from .agent import HealthTechAgent

def main():
    agent = HealthTechAgent()
    print('=== HealthTech EP3 Observabilidad ===')
    print('Escribe una pregunta o "salir" para terminar.')
    while True:
        question = input('\nPregunta: ').strip()
        if question.lower() in {'salir', 'exit', 'q'}:
            print('Sesión finalizada.')
            break
        print('\n' + agent.formatted_response(question))

if __name__ == '__main__':
    main()
