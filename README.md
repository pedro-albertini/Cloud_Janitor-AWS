# ☁️ Cloud Janitor — Automação Inteligente para Redução de Desperdício Financeiro na AWS

<p align="center">
  <img src="./images/arquitetura-cloud-janitor.png" alt="Arquitetura do Cloud Janitor" width="800"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AWS-Cloud-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white"/>
  <img src="https://img.shields.io/badge/AWS_Lambda-Serverless-F90?style=for-the-badge&logo=awslambda&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Boto3-AWS_SDK-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white"/>
  <img src="https://img.shields.io/badge/FinOps-Cost_Optimization-00C853?style=for-the-badge"/>
</p>

---

## 📋 Índice

- [Descrição do Projeto](#-descrição-do-projeto)
- [Problema de Negócio](#-problema-de-negócio)
- [Solução Proposta](#-solução-proposta)
- [Arquitetura e Serviços Utilizados](#️-arquitetura-e-serviços-utilizados)
- [Lógica de Funcionamento](#-lógica-de-funcionamento)
- [Estrutura do Repositório](#-estrutura-do-repositório)
- [Código da Função Lambda](#-código-da-função-lambda)
- [Passo a Passo de Configuração](#-passo-a-passo-de-configuração)
- [Exemplo de Cenário](#-exemplo-de-cenário)
- [Resultado Esperado](#-resultado-esperado)
- [Benefícios do Projeto](#-benefícios-do-projeto)
- [Possíveis Melhorias Futuras](#-possíveis-melhorias-futuras)
- [Aprendizados Aplicados](#-aprendizados-aplicados)
- [Conclusão](#-conclusão)

---

## 📌 Descrição do Projeto

O **Cloud Janitor** é uma automação serverless criada para **reduzir desperdício financeiro em ambientes AWS**.

A solução utiliza **AWS Lambda + Python + Boto3** para identificar instâncias **EC2 em execução** e desligar automaticamente apenas aquelas que:

- ❌ **não estão marcadas como produção**
- ✅ possuem a tag **`AutoStop=true`**

O objetivo é evitar custos desnecessários com ambientes de **desenvolvimento, homologação ou teste** que permanecem ligados fora do horário de uso.

---

## 🚨 Problema de Negócio

Em muitas empresas, desenvolvedores e equipes técnicas criam instâncias EC2 para testes, validações e ambientes temporários. Esses recursos nem sempre são desligados ao final do expediente, permanecendo ativos durante a madrugada, finais de semana e feriados.

Isso gera:

| Problema | Impacto |
|---|---|
| Instâncias ligadas sem uso | Aumento de custo desnecessário |
| Falta de controle sobre ambientes | Baixa governança operacional |
| Recursos ociosos em nuvem | Desperdício financeiro |
| Sem padrão de desligamento | Imprevisibilidade nos custos |

---

## 💡 Solução Proposta

Para resolver esse problema, foi criada uma **automação baseada em eventos**:

```
EventBridge Scheduler → Lambda (Python/Boto3) → EC2 (avalia tags) → Desliga instâncias elegíveis → CloudWatch Logs
```

**Fluxo detalhado:**

1. O **EventBridge Scheduler** agenda a execução da automação em horários definidos
2. A **AWS Lambda** executa o script em Python
3. O **Boto3** consulta a API da AWS buscando instâncias EC2 em estado `running`
4. As **tags** de cada instância são analisadas
5. Instâncias de **produção** são ignoradas e protegidas
6. Instâncias com **`AutoStop=true`** são desligadas automaticamente
7. Toda a execução é registrada no **CloudWatch Logs**

---

## 🏗️ Arquitetura e Serviços Utilizados

<p align="center">
  <img src="./images/diagrama-arquitetura.png" alt="Diagrama de Arquitetura" width="750"/>
</p>

### Serviços AWS

| Serviço | Função |
|---|---|
| **AWS Lambda** | Executa o script Python de automação |
| **Amazon EC2** | Recurso monitorado e controlado pela automação |
| **IAM Role / IAM Policy** | Garante o menor privilégio necessário para a Lambda |
| **Amazon EventBridge Scheduler** | Dispara a Lambda de forma agendada e recorrente |
| **Amazon CloudWatch Logs** | Armazena e centraliza os logs de execução |
| **CloudWatch Billing Alarm** | Monitora custos estimados e evita gastos inesperados |
| **Amazon SNS** | Envia notificações de alerta por e-mail |

---

## 🔎 Lógica de Funcionamento

A automação foi construída com base em **duas tags principais**:

### Tag de ambiente
```
Ambiente = Producao
```
> Se a instância estiver marcada como produção, ela **não será desligada**.

### Tag de autorização para desligamento automático
```
AutoStop = true
```
> Se a instância **não for produção** e possuir `AutoStop=true`, ela **será desligada**.

### Regras de Decisão

```
┌─────────────────────────────────────────────────────────┐
│                  Instância EC2 running                  │
└────────────────────────┬────────────────────────────────┘
                         │
              Ambiente = Producao?
             /                    \
           SIM                    NÃO
            │                      │
         IGNORAR           AutoStop = true?
                          /               \
                        SIM              NÃO
                         │                │
                      DESLIGAR         IGNORAR
```

---

## 📁 Estrutura do Repositório

```
cloud-janitor/
├── README.md
├── lambda_function.py
├── images/
│   ├── arquitetura-cloud-janitor.png
│   ├── diagrama-arquitetura.png
│   ├── iam-role.png
│   ├── iam-policy.png
│   ├── lambda-config.png
│   ├── codigo-lambda.png
│   ├── ec2-tags.png
│   ├── teste-lambda.png
│   ├── cloudwatch-logs.png
│   ├── eventbridge-scheduler.png
│   └── billing-alarm.png
└── docs/
    └── observacoes.md
```

---

## 🐍 Código da Função Lambda

```python
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
```

---

## 🚀 Passo a Passo de Configuração

### 1️⃣ Criar o Billing Alarm

Antes de iniciar, configure um **Billing Alarm** para monitorar custos e evitar surpresas.

**Configuração adotada:**
- Limite de alerta: **US$ 0,50**
- Notificação por e-mail via **SNS**

<p align="center">
  <img src="./images/billing-alarm.png" alt="Billing Alarm" width="700"/>
</p>

---

### 2️⃣ Criar a IAM Policy Customizada

Crie uma policy com **permissões mínimas** para a Lambda (princípio do menor privilégio):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DescribeAndStopEC2",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:StopInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

<p align="center">
  <img src="./images/iam-policy.png" alt="IAM Policy" width="700"/>
</p>

---

### 3️⃣ Criar a IAM Role da Lambda

Crie uma role específica para a função Lambda com:

- Trust relationship para `lambda.amazonaws.com`
- Policy customizada de EC2
- `AWSLambdaBasicExecutionRole` para permissão de logs

<p align="center">
  <img src="./images/iam-role.png" alt="IAM Role" width="700"/>
</p>

---

### 4️⃣ Criar a Função Lambda

| Configuração | Valor |
|---|---|
| Nome | `cloud-janitor-ec2-auto-stop` |
| Runtime | Python 3.12 |
| Arquitetura | x86_64 |
| Role | CloudJanitorLambdaRole |

<p align="center">
  <img src="./images/lambda-config.png" alt="Configuração da Lambda" width="700"/>
</p>

---

### 5️⃣ Inserir o Código Python

Cole o código da função no editor da Lambda e faça o **Deploy**.

<p align="center">
  <img src="./images/codigo-lambda.png" alt="Código Lambda no Console AWS" width="700"/>
</p>

---

### 6️⃣ Configurar as Tags na Instância EC2

Configure as tags nas instâncias conforme a regra de negócio:

| Tag | Valor | Comportamento |
|---|---|---|
| `Ambiente` | `Producao` | Instância **protegida**, nunca será desligada |
| `Ambiente` | `Dev` / `Teste` / qualquer outro | Elegível para avaliação |
| `AutoStop` | `true` | Instância **será desligada** (se não for produção) |

<p align="center">
  <img src="./images/ec2-tags.png" alt="Tags da EC2" width="700"/>
</p>

---

### 7️⃣ Testar a Lambda Manualmente

Execute um teste manual com o evento:

```json
{}
```

O teste valida:
- ✅ Acesso à EC2
- ✅ Leitura das tags
- ✅ Aplicação da regra de negócio
- ✅ Desligamento automático da instância elegível

<p align="center">
  <img src="./images/teste-lambda.png" alt="Teste Manual da Lambda" width="700"/>
</p>

---

### 8️⃣ Validar os Logs no CloudWatch

Após a execução, analise os logs no **CloudWatch** para validar o comportamento da automação.

<p align="center">
  <img src="./images/cloudwatch-logs.png" alt="CloudWatch Logs" width="700"/>
</p>

---

### 9️⃣ Criar o Agendamento com EventBridge Scheduler

Configure a execução recorrente via **EventBridge Scheduler**.

**Exemplo de uso:** execução diária às `20:00` para desligar ambientes não produtivos ao fim do expediente.

<p align="center">
  <img src="./images/eventbridge-scheduler.png" alt="EventBridge Scheduler" width="700"/>
</p>

---

## 🧪 Exemplo de Cenário

| Instância | Tags | Resultado |
|---|---|---|
| Instância 1 | `Ambiente=Producao`, `AutoStop=true` | ✅ **Ignorada** — protegida por ser produção |
| Instância 2 | `Ambiente=Dev`, `AutoStop=true` | 🔴 **Desligada** — elegível para auto stop |
| Instância 3 | `Ambiente=Teste` (sem AutoStop) | ✅ **Ignorada** — sem a tag AutoStop=true |

---

## ✅ Resultado Esperado

Ao executar a Lambda, o retorno será semelhante a:

```json
{
  "statusCode": 200,
  "body": {
    "mensagem": "Execução concluída com sucesso.",
    "instancias_desligadas": [
      "i-xxxxxxxxxxxxxxxxx"
    ],
    "instancias_ignoradas": []
  }
}
```

---

## 💰 Benefícios do Projeto

- 📉 Redução de desperdício financeiro em nuvem
- 🤖 Automação de rotina operacional
- 💡 Aplicação prática de **FinOps**
- ☁️ Uso de arquitetura **serverless**
- 🏷️ Controle de ambientes por tags
- 🔐 Governança com princípio do menor privilégio

---

## 🔮 Possíveis Melhorias Futuras

- [ ] Ligar instâncias automaticamente pela manhã
- [ ] Enviar relatório por e-mail com resumo da execução via SNS
- [ ] Adicionar suporte a múltiplas regiões AWS
- [ ] Criar dashboards de monitoramento no CloudWatch
- [ ] Implementar a infraestrutura como código com **Terraform**
- [ ] Expandir a lógica para outros recursos como **RDS**, **ECS tasks**, etc.

---

## 📚 Aprendizados Aplicados

Este projeto permitiu praticar na prática:

- `AWS Lambda` — funções serverless orientadas a eventos
- `Amazon EC2` — gerenciamento e automação de instâncias
- `IAM` — princípio do menor privilégio
- `EventBridge Scheduler` — agendamento de execuções
- `CloudWatch Logs` — observabilidade e rastreabilidade
- `Billing Alarm` — monitoramento de custos
- `Python + Boto3` — automação de infraestrutura AWS
- `FinOps` — otimização de custos em nuvem
- `Governança por tags` — padrão de classificação de recursos

---

## 🏁 Conclusão

O **Cloud Janitor** é uma solução prática de automação serverless com foco em **otimização de custos na AWS**.

A proposta demonstra como pequenas rotinas automatizadas podem gerar ganho real de **governança, previsibilidade e eficiência operacional** em ambientes cloud — sem necessidade de servidores dedicados e com custo operacional praticamente zero.

Além do aspecto técnico, o projeto reforça a importância de práticas de **FinOps**, uso consciente de recursos e automações seguras baseadas em **tags e permissões mínimas**.

---

<p align="center">
  Desenvolvido com ☁️ e 🐍 utilizando AWS Lambda, Python e Boto3
</p>
