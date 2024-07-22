package main

import (
	"context"
	"time"
	"log"
	"errors"

	"github.com/paralin/go-dota2"
	"github.com/paralin/go-dota2/protocol"
	"github.com/paralin/go-dota2/state"
	"github.com/paralin/go-steam"
	"github.com/paralin/go-steam/protocol/steamlang"
	"github.com/paralin/go-dota2/cso"
	"github.com/paralin/go-steam/steamid"
	"github.com/sirupsen/logrus"
	"google.golang.org/protobuf/proto"
)

func main() {
	steamClient := steam.NewClient()
	steam.InitializeSteamDirectory()

	logOnDetails := &steam.LogOnDetails{
		Username:               "",
		Password:               "",
		// AuthCode:               "V6N2V",
		TwoFactorCode :			"dgdrf",
		ShouldRememberPassword: true,
	}

	var dotaClient *dota2.Dota2

	steamClient.Connect()
	for event := range steamClient.Events() {
		switch event.(type) {

		case *steam.ConnectedEvent:
			steamClient.Auth.LogOn(logOnDetails)

		case *steam.LoggedOnEvent:
			steamClient.Social.SetPersonaState(steamlang.EPersonaState_LookingToPlay)
			logger := logrus.New()
			logger.Level = logrus.DebugLevel
			dotaClient = dota2.New(steamClient, logger)
			dotaClient.SetPlaying(true)

			time.Sleep(1 * time.Second)

			dotaClient.SayHello()
			go func() {
				ticker := time.NewTicker(2 * time.Second)
				for range ticker.C {
					dotaClient.SayHello()
				}
			}()

			dota2s := state.Dota2State{}
			if dota2s.IsReady() {
				// Create the lobby
				_, err := createLobby(dotaClient)
				if err != nil {
					log.Println("Failed to create lobby:", err)
					return
				}

				time.Sleep(1 * time.Second)

				log.Println("Inviting friends")

				dotaClient.KickLobbyMemberFromTeam(steamClient.SteamId().GetAccountId())
				friendId := steamid.SteamId(uint64(76561198113427529)) // steam id
				dotaClient.InviteLobbyMember(friendId)

				time.Sleep(10 * time.Second)

				log.Println("Going to start the game")
				dotaClient.LaunchLobby()
			}
		}
	}
}

func createLobby(dotaClient *dota2.Dota2) (*protocol.CSODOTALobby, error) {
	log.Println("Setting up lobby...")

	time.Sleep(3 * time.Second)
	
	lobby, err := GetCurrentLobby(dotaClient)
	if err != nil {
		log.Println("Failed to get an old/existing lobby:", err)
	}

	if lobby != nil {
		log.Println("Destroying old lobby")

		if res, err := dotaClient.DestroyLobby(context.Background()); err != nil {
			log.Println("Failed to destroy lobby: ", err, res)
			// return nil, err
		}

		// lob := lobby.(*protocol.CSODOTALobby)
		if lobby.GetState() != protocol.CSODOTALobby_UI {
			dotaClient.AbandonLobby()
		}
		dotaClient.LeaveLobby()
	}
	dotaClient.LeaveLobby()
	dotaClient.AbandonLobby()


	time.Sleep(3 * time.Second)
	
	// dotaClient.LeaveCreateLobby(context.Background(), &protocol.CMsgPracticeLobbySetDetails{}

	// https://github.com/paralin/go-dota2/blob/e8f172852608601dcb13ebc8aa442ced27938ad5/protocol/dota_gcmessages_client_match_management.proto#L116
	// https://github.com/paralin/go-dota2/blob/master/protocol/dota_shared_enums.proto
	lobbyDetails := &protocol.CMsgPracticeLobbySetDetails{
		GameName:         proto.String("lobbytest"),
		PassKey:          proto.String("123"),
		GameMode:         proto.Uint32(1),
		CustomGameId:     proto.Uint64(18446744072660900618),
		AllowCheats:      proto.Bool(true),
		FillWithBots:     proto.Bool(true),
		AllowSpectating:  proto.Bool(true),
		Visibility:       protocol.DOTALobbyVisibility_DOTALobbyVisibility_Public.Enum(),
		BotRadiant:       proto.Uint64(18446744072660900618),
		BotDire:          proto.Uint64(18446744072660900618),
		BotDifficultyDire:  protocol.DOTABotDifficulty_BOT_DIFFICULTY_UNFAIR.Enum(),
		BotDifficultyRadiant:  protocol.DOTABotDifficulty_BOT_DIFFICULTY_UNFAIR.Enum(),
	}

	log.Println("Creating new lobby")
	dotaClient.CreateLobby(lobbyDetails)
	for i := 0; i < 5; i++ {
		time.Sleep(2 * time.Second)
		lobby, err := GetCurrentLobby(dotaClient)
		if err != nil {
			log.Println("Failed to get lobby:", err)
		} else {
			log.Println("New lobby created")
			return lobby, nil
		}
	}
	
	// lobby, err := dotaClient.GetCache().GetContainerForTypeID(cso.Lobby)
	// if err != nil {
	// 	log.Println("Failed to get lobby:", err)
	// }
	// lobbyMessage := lobby.GetOne()
	// if lobbyMessage != nil {
	// 	log.Println("no lobby found:", lobbyMessage)
	// } else {
	// 	log.Println("found lobby, invite friends")
	// 	dotaClient.KickLobbyMemberFromTeam(steamClient.SteamId().GetAccountId())
	// 	friendId := steamid.SteamId(uint64(76561198113427529)) // steam id
	// 	dotaClient.InviteLobbyMember(friendId)
	// }

	return nil, errors.New("failed to create lobby")
}

func GetCurrentLobby(dotaClient *dota2.Dota2) (*protocol.CSODOTALobby, error) {
	_, err := dotaClient.GetCache().GetContainerForTypeID(cso.Lobby)
	if err != nil {
		log.Println("Error while trying to get lobby:", err)
		return nil, err
	}

	// lobbyMessage := lobby.GetOne()
	// if lobbyMessage == nil {
	// 	return nil, errors.New("no lobby found")
	// }

	return nil, nil
}
