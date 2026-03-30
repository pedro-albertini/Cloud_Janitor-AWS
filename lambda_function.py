import boto3

def lambda_handler(event, context):
    ec2 = boto3.resource('ec2')
    
    # Filtra apenas instâncias que estão ligadas
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )

    instancias_desligadas = []
    instancias_ignoradas = []

    for instance in instances:
        # Transforma as tags em dicionário para facilitar a leitura
        tags = {tag['Key']: tag['Value'] for tag in instance.tags} if instance.tags else {}

        ambiente = tags.get('Ambiente')
        auto_stop = tags.get('AutoStop')

        # Regra 1: se for produção, não desliga
        if ambiente == 'Producao':
            instancias_ignoradas.append(f'{instance.id} - ignorada por ser produção')
            continue

        # Regra 2: só desliga se tiver AutoStop=true
        if auto_stop != 'true':
            instancias_ignoradas.append(f'{instance.id} - ignorada por não ter AutoStop=true')
            continue

        # Se passou nas regras, desliga a instância
        instance.stop()
        instancias_desligadas.append(instance.id)
        print(f'Instância {instance.id} desligada com sucesso.')

    return {
        'statusCode': 200,
        'body': {
            'mensagem': 'Execução concluída com sucesso.',
            'instancias_desligadas': instancias_desligadas,
            'instancias_ignoradas': instancias_ignoradas
        }
    }