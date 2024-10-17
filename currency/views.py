
from asyncio import exceptions
from rest_framework import generics
from rest_framework.views import APIView
from currency.models import Currency, ExchangeRate
from currency.serializers import CurrencySerializer, ExchangeRateSerializer
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

# class CurrencyListView(generics.ListAPIView):
#     queryset = Currency.objects.all()
#     serializer_class = CurrencySerializer

#     def get(self, request, *args, **kwargs):
#         try:
#             currencies = self.get_queryset()
#             serilizer = self.get_serializer(currencies, many=True)
#             return Response(serilizer.data, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class CurrencyView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            currencies = Currency.objects.all()
            serializer = CurrencySerializer(currencies, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        serializer = CurrencySerializer(data=request.data)

        # Проверка на наличие необходимых полей
        if not request.data.get('currency_code') or not request.data.get('currency_full_name') or not request.data.get('sign'):
            return Response({"detail": "Отсутствует нужное поле формы."}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на уникальность кода валюты
        if Currency.objects.filter(currency_code=request.data['currency_code']).exists():
            return Response({"detail": "Валюта с таким кодом уже существует."}, status=status.HTTP_409_CONFLICT)

        if serializer.is_valid():
            currency = serializer.save()  # Сохранение новой валюты
            return Response(CurrencySerializer(currency).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        



class CurrencyDetailView(generics.RetrieveAPIView):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    lookup_field = 'currency_code'  # Поле, по которому будет осуществляться поиск

    def get(self, request, *args, **kwargs):
        code = kwargs.get('currency_code')
        
        # Проверка на наличие кода валюты в запросе
        if not code:
            return Response({"detail": "Код валюты отсутствует в адресе."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            currency = self.get_object()  # Получаем объект валюты по коду
            serializer = self.get_serializer(currency)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Currency.DoesNotExist:
            return Response({"detail": "Валюта не найдена."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



class ExchangeView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            rates = ExchangeRate.objects.all()
            serializer = ExchangeRateSerializer(rates, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        # Extracting fields from the request
        base_currency_code = request.data.get('baseCurrencyCode')
        target_currency_code = request.data.get('targetCurrencyCode')
        rate = request.data.get('rate')

        # Проверка на наличие необходимых полей
        if not base_currency_code or not target_currency_code or rate is None:
            return Response({"detail": "Отсутствует нужное поле формы.", "base_currency_code": base_currency_code,
                "target_currency_code": target_currency_code,
                "rate": rate}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на существование валют
        try:
            base_currency = Currency.objects.get(currency_code=base_currency_code)
            target_currency = Currency.objects.get(currency_code=target_currency_code)
        except Currency.DoesNotExist:
            return Response({"detail": "Одна (или обе) валюта из валютной пары не существует в БД."}, status=status.HTTP_404_NOT_FOUND)

        # Проверка на уникальность обменного курса
        if ExchangeRate.objects.filter(base_currency=base_currency, target_currency=target_currency).exists():
            return Response({"detail": "Валютная пара с таким кодом уже существует."}, status=status.HTTP_409_CONFLICT)

        # Создание и сохранение нового обменного курса
        exchange_rate = ExchangeRate(base_currency=base_currency, target_currency=target_currency, rate=rate)
        exchange_rate.save()  # Save the new exchange rate

        # Return the serialized data of the newly created exchange rate
        serializer = ExchangeRateSerializer(exchange_rate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

    


class ExchangeDetailView(generics.RetrieveUpdateAPIView):
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    lookup_field = 'currency_pair'  # Будем использовать валютную пару из URL

    def get_object(self):
        # Извлечение валютной пары из URL
        currency_pair = self.kwargs['currency_pair']

        if not currency_pair or len(currency_pair) != 6:
            return Response({"detail": "Коды валют пары отсутствуют в адресе."}, status=status.HTTP_400_BAD_REQUEST)

        # Разделяем валютную пару на базовую и целевую валюты
        base_currency_code = currency_pair[:3]
        target_currency_code = currency_pair[3:]

        try:
            # Возвращаем объект ExchangeRate по базовой и целевой валюте
            return ExchangeRate.objects.get(
                base_currency__currency_code=base_currency_code,
                target_currency__currency_code=target_currency_code
            )
        except ExchangeRate.DoesNotExist:
            return Response({"detail": "Обменный курс для пары не найден."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        # Извлечение данных из тела запроса
        rate = request.data.get('rate')

        if rate is None:
            return Response({"detail": "Отсутствует нужное поле формы 'rate'."}, status=status.HTTP_400_BAD_REQUEST)

        # Попробуем получить запись для обновления
        exchange_rate = self.get_object()
        
        if isinstance(exchange_rate, Response):  # Если get_object вернул Response с ошибкой
            return exchange_rate

        try:
            # Обновляем курс
            exchange_rate.rate = rate
            exchange_rate.save()

            # Формируем и возвращаем ответ с обновленной информацией
            serializer = self.get_serializer(exchange_rate)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class CurrencyExchangeView(APIView):
    def get(self, request, *args, **kwargs):
        # Получаем параметры запроса
        base_currency_code = request.query_params.get('from')
        target_currency_code = request.query_params.get('to')
        amount = request.query_params.get('amount')
        exchange_rate = None
        reverse_exchange_rate = None
        conversion_rate = None

        if not base_currency_code or not target_currency_code or not amount:
            return Response({"detail": "Отсутствуют необходимые параметры 'from', 'to' или 'amount'."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(amount)
        except ValueError:
            return Response({"detail": "Неверный формат параметра 'amount'."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Сценарий 1: Валютная пара AB существует
            exchange_rate = ExchangeRate.objects.get(
                base_currency__currency_code=base_currency_code,
                target_currency__currency_code=target_currency_code
            )
            conversion_rate = exchange_rate.rate

        except ExchangeRate.DoesNotExist:
            try:
                # Сценарий 2: Валютная пара BA существует (инвертируем курс)
                reverse_exchange_rate = ExchangeRate.objects.get(
                    base_currency__currency_code=target_currency_code,
                    target_currency__currency_code=base_currency_code
                )
                conversion_rate = 1 / reverse_exchange_rate.rate

            except ExchangeRate.DoesNotExist:
                try:
                    # Сценарий 3: Используем USD в качестве промежуточной валюты
                    usd_currency = Currency.objects.get(currency_code='USD')
                    
                    # Найти курсы USD-A и USD-B
                    usd_to_base = ExchangeRate.objects.get(
                        base_currency=usd_currency,
                        target_currency__currency_code=base_currency_code
                    )
                    usd_to_target = ExchangeRate.objects.get(
                        base_currency=usd_currency,
                        target_currency__currency_code=target_currency_code
                    )
                    
                    # Вычисляем курс AB через USD
                    conversion_rate = usd_to_target.rate / usd_to_base.rate

                except (ExchangeRate.DoesNotExist, Currency.DoesNotExist):
                    return Response({"detail": "Не удалось найти курс обмена для указанных валют."},
                                    status=status.HTTP_404_NOT_FOUND)

        # Вычисление суммы в целевой валюте
        converted_amount = amount * conversion_rate


        # Используем сериализатор для формирования ответа
        response_data = {}
        
        response_data['base_currency'] = CurrencySerializer(Currency.objects.get(currency_code=base_currency_code)).data
        response_data['target_currency'] = CurrencySerializer(Currency.objects.get(currency_code=target_currency_code)).data
        response_data['rate'] = conversion_rate
        response_data['amount'] = amount
        response_data['convertedAmount'] = converted_amount

        return Response(response_data, status=status.HTTP_200_OK)