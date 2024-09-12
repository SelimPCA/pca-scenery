from http import HTTPMethod


from app.tests.views.dataclasses import HttpTake


class IO:

    @staticmethod
    def get_http_client_response(client, take: HttpTake):

        # print("###########", take)

        match take.method:
            case HTTPMethod.GET:
                response = client.get(
                    take.url,
                    take.data,
                )
            case HTTPMethod.POST:
                response = client.post(
                    take.url,
                    take.data,
                )
            case _:
                raise NotImplementedError(take.method)
        return response
